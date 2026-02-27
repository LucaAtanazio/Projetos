const fs = require('fs');
const path = require('path');
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

const rankingPath = path.join(__dirname, 'ranking.json');
if (!fs.existsSync(rankingPath)) fs.writeFileSync(rankingPath, JSON.stringify([]));

// --- CONFIGURAÇÕES ---
const HUD_HEIGHT = 50; 
const CORES = {
    PLAYER: "#00FA9A", SPARX: "#FF69B4", LINHAS: "#FFE4B5",
    MORTE: "#FF0000", FUNDO: "#000015", AREA: "#4169E1"
};
const ROWS = 80, COLS = 120; 
const cellW = canvas.width / COLS;
const cellH = (canvas.height - HUD_HEIGHT) / ROWS;

let player, qix, sparx, grid, gameState = "START_MENU";
let menuIndex = 0, areaConquistada = 0, metaArea = 0;
let startTime, finalTimeStr = "00:00:00", deathParticles = [];
const keys = {};

// --- INICIALIZAÇÃO GEOMÉTRICA ---
function initGame() {
    player = { 
        x: 0, y: HUD_HEIGHT, isDrawing: false, speed: 4, 
        lives: 3, invencivel: false, blink: 0 
    };
    
    areaConquistada = 0;
    metaArea = Math.floor(Math.random() * 15) + 65;
    startTime = performance.now();
    grid = Array(ROWS).fill().map(() => Array(COLS).fill(0));
    
    // Moldura Física (grid === 1)
    for(let r=0; r<ROWS; r++) {
        for(let c=0; c<COLS; c++) {
            if(r===0 || r===ROWS-1 || c===0 || c===COLS-1) grid[r][c] = 1;
        }
    }
    
    // Sparks com Estética Original
    sparx = [
        { x: 0, y: HUD_HEIGHT, dir: 'right', speed: 2.5 },
        { x: canvas.width - 5, y: HUD_HEIGHT, dir: 'left', speed: 2.5 }
    ];

    // Qix com Rastro Arco-íris (history)
    qix = { 
        x: canvas.width/2, 
        y: player.y + (canvas.height - HUD_HEIGHT)/2, 
        vx: 2.5, vy: 2.5, angle: 0, spin: 0.2, history: [] 
    };
    
    gameState = "PLAYING";
}

// --- CONTROLES (RESTAURADOS) ---
window.addEventListener("keydown", (e) => {
    keys[e.code] = true;
    if (gameState === "START_MENU" || gameState === "RANKING_VIEW") {
        if (e.code === "ArrowUp" || e.code === "KeyW") menuIndex = 0;
        if (e.code === "ArrowDown" || e.code === "KeyS") menuIndex = 1;
        if (e.code === "Enter" || e.code === "Space") {
            if (gameState === "RANKING_VIEW") gameState = "START_MENU";
            else if (menuIndex === 0) initGame();
            else gameState = "RANKING_VIEW";
        }
    }
});
window.addEventListener("keyup", (e) => { keys[e.code] = false; });

// --- LÓGICA DE MORTE E REVERSO TEMPORAL ---
function triggerDeath() {
    if (gameState !== "PLAYING") return;
    gameState = "DYING";
    const angles = [45, 135, 225, 315];
    deathParticles = angles.map(a => ({
        x: player.x, y: player.y,
        vx: Math.cos(a * Math.PI / 180) * 10, vy: Math.sin(a * Math.PI / 180) * 10,
        life: 40, returning: false
    }));
}

function handleRespawnLogic() {
    deathParticles.forEach(p => {
        if (!p.returning) {
            p.x += p.vx; p.y += p.vy;
            if (p.life <= 20) p.returning = true;
        } else {
            p.x -= p.vx; p.y -= p.vy;
        }
        p.life--;
    });

    if (deathParticles[0].life <= 0) {
        player.lives--;
        if (player.lives <= 0) { gameState = "START_MENU"; return; }
        const safeX = (Math.random() > 0.5) ? 0 : canvas.width - 5;
        player.x = safeX; player.y = HUD_HEIGHT;
        player.invencivel = true; player.blink = 0;
        replaceValueInGrid(2, 0);
        gameState = "PLAYING";
    }
}

// --- UPDATE ---
function update() {
    if (gameState === "DYING") { handleRespawnLogic(); return; }
    if (gameState !== "PLAYING") return;

    if (player.invencivel) { player.blink++; if (player.blink > 100) player.invencivel = false; }

    // QIX + RASTRO (HISTORY)
    qix.x += qix.vx; qix.y += qix.vy; qix.angle += qix.spin;
    let qgx = Math.floor(qix.x / cellW), qgy = Math.floor((qix.y - HUD_HEIGHT) / cellH);

    if (grid[qgy]) {
        if (grid[qgy][qgx + 1] !== 0 || grid[qgy][qgx - 1] !== 0) qix.vx *= -1;
        if ((grid[qgy + 1] && grid[qgy + 1][qgx] !== 0) || (grid[qgy - 1] && grid[qgy - 1][qgx] !== 0)) qix.vy *= -1;
        if (grid[qgy][qgx] === 2) triggerDeath();
    }

    qix.history.push({x: qix.x, y: qix.y, angle: qix.angle});
    if (qix.history.length > 15) qix.history.shift();

    // SPARX + PATRULHA
    sparx.forEach(s => {
        if (s.dir === 'right') { s.x += s.speed; if (s.x >= canvas.width-5) s.dir = 'down'; }
        else if (s.dir === 'down') { s.y += s.speed; if (s.y >= canvas.height-5) s.dir = 'left'; }
        else if (s.dir === 'left') { s.x -= s.speed; if (s.x <= 0) s.dir = 'up'; }
        else if (s.dir === 'up') { s.y -= s.speed; if (s.y <= HUD_HEIGHT) s.dir = 'right'; }
        if (!player.invencivel && Math.hypot(s.x - player.x, s.y - player.y) < 15) triggerDeath();
    });

    handlePlayerMovement();
}

function handlePlayerMovement() {
    let dx = 0, dy = 0;
    if (keys['ArrowUp'] || keys['KeyW']) dy = -player.speed;
    if (keys['ArrowDown'] || keys['KeyS']) dy = player.speed;
    if (keys['ArrowLeft'] || keys['KeyA']) dx = -player.speed;
    if (keys['ArrowRight'] || keys['KeyD']) dx = player.speed;

    if (dx !== 0 || dy !== 0) {
        let nX = Math.max(0, Math.min(canvas.width - 5, player.x + dx));
        let nY = Math.max(HUD_HEIGHT, Math.min(canvas.height - 5, player.y + dy));
        let gX = Math.floor(nX/cellW), gY = Math.floor((nY-HUD_HEIGHT)/cellH);

        if (keys['Space']) {
            if (grid[gY] && grid[gY][gX] === 0) { grid[gY][gX] = 2; player.isDrawing = true; } 
            else if (grid[gY] && (grid[gY][gX] === 1 || grid[gY][gX] === 3) && player.isDrawing) finalizeCut();
            player.x = nX; player.y = nY;
        } else if (grid[gY] && (grid[gY][gX] === 1 || grid[gY][gX] === 3)) {
            player.x = nX; player.y = nY; player.isDrawing = false;
        }
    }
}

// --- RENDER ---
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (gameState === "START_MENU") {
        drawMenu("QIX ARCADE", ["INICIAR JOGO", "RANKING"]);
    } else if (gameState === "RANKING_VIEW") {
        drawRanking();
    } else {
        ctx.fillStyle = CORES.FUNDO; ctx.fillRect(0, HUD_HEIGHT, canvas.width, canvas.height - HUD_HEIGHT);
        
        // Grid
        for(let r=0; r<ROWS; r++) {
            for(let c=0; c<COLS; c++) {
                if (grid[r][c] === 1) ctx.fillStyle = CORES.LINHAS;
                else if (grid[r][c] === 2) ctx.fillStyle = CORES.MORTE;
                else if (grid[r][c] === 3) ctx.fillStyle = CORES.AREA;
                else continue;
                ctx.fillRect(c*cellW, r*cellH + HUD_HEIGHT, cellW + 1, cellH + 1);
            }
        }

        // QIX RAINBOW (ESTÉTICA RESTAURADA)
        qix.history.forEach((h, i) => {
            ctx.strokeStyle = `hsla(${(i*20 + Date.now()/10)%360}, 100%, 50%, ${i/15})`;
            ctx.lineWidth = 3; ctx.beginPath();
            ctx.moveTo(h.x + Math.cos(h.angle)*25, h.y + Math.sin(h.angle)*25);
            ctx.lineTo(h.x - Math.cos(h.angle)*25, h.y - Math.sin(h.angle)*25); ctx.stroke();
        });

        // SPARX + FAÍSCAS (ESTÉTICA RESTAURADA)
        sparx.forEach(s => {
            ctx.fillStyle = CORES.SPARX; ctx.beginPath(); ctx.arc(s.x, s.y, 8, 0, Math.PI*2); ctx.fill();
            ctx.fillStyle = "#FFF";
            for(let i=0; i<3; i++) ctx.fillRect(s.x+(Math.random()-0.5)*20, s.y+(Math.random()-0.5)*20, 2, 2);
        });

        // PLAYER
        if (gameState === "DYING") {
            ctx.fillStyle = "#FFF"; deathParticles.forEach(p => ctx.fillRect(p.x, p.y, 5, 5));
        } else if (!player.invencivel || Math.floor(Date.now()/100)%2===0) {
            ctx.fillStyle = CORES.PLAYER; ctx.fillRect(player.x-7, player.y-7, 14, 14);
        }
        drawHUD();
    }
}

function drawMenu(t, o) {
    ctx.textAlign="center"; ctx.fillStyle=CORES.PLAYER; ctx.font="bold 40px 'Courier New'"; ctx.fillText(t, canvas.width/2, canvas.height/2-50);
    o.forEach((opt, i) => { ctx.fillStyle=(menuIndex===i)?"#FFF":"#555"; ctx.font="20px 'Courier New'"; ctx.fillText(`${menuIndex===i?"> ":""}${opt}`, canvas.width/2, canvas.height/2+20+(i*40)); });
}

function drawRanking() {
    ctx.textAlign = "center"; ctx.fillStyle = CORES.PLAYER; ctx.font = "28px 'Courier New'";
    ctx.fillText("RANKING DOS MELHORES", canvas.width/2, 150);
    let rk = []; try { rk = JSON.parse(fs.readFileSync(rankingPath)).slice(0, 5); } catch(e) {}
    rk.forEach((item, i) => {
        ctx.fillStyle = "#FFF"; ctx.fillText(`${i+1}. ${item.nome} - ${item.tempo}`, canvas.width/2, 220 + (i*30));
    });
    ctx.fillStyle = CORES.PLAYER; ctx.fillText("> VOLTAR (ENTER)", canvas.width/2, canvas.height - 80);
}

function drawHUD() {
    ctx.fillStyle="#000"; ctx.fillRect(0,0, canvas.width, HUD_HEIGHT);
    ctx.fillStyle="#FFF"; ctx.font="bold 16px 'Courier New'"; ctx.textAlign="left";
    ctx.fillText(`VIDAS: ${player.lives} | ÁREA: ${areaConquistada}% / ${metaArea}%`, 20, 30);
}

// Funções auxiliares (Floodfill/Finalize)
function finalizeCut() {
    replaceValueInGrid(2, 1);
    let qx = Math.floor(qix.x / cellW), qy = Math.floor((qix.y - HUD_HEIGHT) / cellH);
    if (grid[qy] && grid[qy][qx] === 0) floodFill(qx, qy, 0, 4);
    for (let r=0; r<ROWS; r++) for (let c=0; c<COLS; c++) if (grid[r][c] === 0) grid[r][c] = 3;
    replaceValueInGrid(4, 0); player.isDrawing = false; calculateArea();
}

function floodFill(x, y, target, replacement) {
    let stack = [[x, y]];
    while(stack.length > 0) {
        let [cx, cy] = stack.pop();
        if (cx >= 0 && cx < COLS && cy >= 0 && cy < ROWS && grid[cy][cx] === target) {
            grid[cy][cx] = replacement;
            stack.push([cx+1, cy], [cx-1, cy], [cx, cy+1], [cx, cy-1]);
        }
    }
}

function calculateArea() {
    let p = 0; for (let r=1; r<ROWS-1; r++) for (let c=1; c<COLS-1; c++) if (grid[r][c] === 3) p++;
    areaConquistada = Math.floor((p / ((ROWS-2)*(COLS-2))) * 100);
}

function replaceValueInGrid(o,n) { for(let r=0;r<ROWS;r++) for(let c=0;c<COLS;c++) if(grid[r][c]===o) grid[r][c]=n; }

function gameLoop() { update(); draw(); requestAnimationFrame(gameLoop); }
gameLoop();