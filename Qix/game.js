const fs = require('fs');
const path = require('path');
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

const rankingPath = path.join(__dirname, 'ranking.json');
if (!fs.existsSync(rankingPath)) fs.writeFileSync(rankingPath, JSON.stringify([]));

// --- CONFIGURAÇÕES ---
const CORES = {
    PLAYER: "#00FA9A", SPARX: "#FF69B4", LINHAS: "#FFE4B5",
    MORTE: "#FF0000", FUNDO: "#000044", AREA: "#4169E1", HUD: "#FFFFFF"
};
const ROWS = 80, COLS = 120; // Reduzi levemente a grade para maior estabilidade no floodFill
const cellW = canvas.width / COLS, cellH = canvas.height / ROWS;

let player, qix, sparx, grid, gameState = "START_MENU";
let menuIndex = 0, areaConquistada = 0, metaArea = 0;
let startTime, finalTimeStr = "00:00:00", nomePlayer = "";
const keys = {};

// --- INICIALIZAÇÃO ---
function initGame() {
    player = { x: 0, y: 0, isDrawing: false, speed: 4, size: 12, lives: 3, invencivel: false, blink: 0 };
    areaConquistada = 0;
    metaArea = Math.floor(Math.random() * 15) + 65;
    startTime = performance.now();
    grid = Array(ROWS).fill().map(() => Array(COLS).fill(0));
    
    for(let r=0; r<ROWS; r++) {
        for(let c=0; c<COLS; c++) {
            if(r===0 || r===ROWS-1 || c===0 || c===COLS-1) grid[r][c] = 1;
        }
    }
    
    const vS = player.speed * 0.6;
    sparx = [
        { x: 40 * cellW, y: 0, dir: 'right', speed: vS },
        { x: (COLS - 40) * cellW, y: 0, dir: 'left', speed: vS }
    ];
    qix = { x: canvas.width/2, y: canvas.height/2, vx: 2.5, vy: 2.5, angle: 0, spin: 0.1 };
    gameState = "PLAYING";
}

// --- CONTROLES ---
window.onkeydown = (e) => {
    if (gameState === "PLAYING") keys[e.code] = true;
    if (["START_MENU", "GAME_WIN", "RANKING_VIEW"].includes(gameState)) {
        if (e.code === "ArrowUp" || e.code === "ArrowDown") menuIndex = (menuIndex === 0 ? 1 : 0);
        if (e.code === "Enter" || e.code === "Space") {
            if (gameState === "RANKING_VIEW") gameState = "START_MENU";
            else if (menuIndex === 0) initGame();
            else gameState = "RANKING_VIEW";
        }
    }
    if (gameState === "INPUT_NAME") {
        if (e.key === "Enter" && nomePlayer.length > 0) salvarRecorde();
        else if (e.key === "Backspace") nomePlayer = nomePlayer.slice(0, -1);
        else if (nomePlayer.length < 13 && e.key.length === 1) nomePlayer += e.key.toUpperCase();
    }
};
window.onkeyup = (e) => keys[e.code] = false;

// --- LÓGICA DE PREENCHIMENTO (SOLUÇÃO DO BUG) ---



function finalizeCut() {
    // 1. O rastro (2) vira borda (1)
    replaceValueInGrid(2, 1);
    
    // Pegamos a posição atual do Qix convertida para a grade
    let qx = Math.floor(qix.x / cellW);
    let qy = Math.floor(qix.y / cellH);

    // 2. Identificar áreas vazias
    // Usamos um valor temporário 4 para mapear onde o Qix está
    // Primeiro, inundamos a área onde o Qix está a partir da posição dele
    if (grid[qy] && grid[qy][qx] === 0) {
        floodFill(qx, qy, 0, 4); 
    } else {
        // Se o Qix estiver em cima de algo que não é 0 (raro), procura o 0 mais próximo
        encontrarEspacoVazioParaQix(qx, qy);
    }

    // 3. Agora, qualquer 0 que sobrou NÃO contém o Qix e deve ser preenchido
    for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
            if (grid[r][c] === 0) {
                grid[r][c] = 3; // Preenche a ilha conquistada
            }
        }
    }

    // 4. Devolvemos a área do Qix (4) para vazio (0)
    replaceValueInGrid(4, 0);
    
    player.isDrawing = false;
    calculateArea();
}

function floodFill(x, y, target, replacement) {
    if (x < 0 || x >= COLS || y < 0 || y >= ROWS || grid[y][x] !== target) return;
    let stack = [[x, y]];
    while(stack.length > 0) {
        let [cx, cy] = stack.pop();
        if (grid[cy][cx] === target) {
            grid[cy][cx] = replacement;
            if (cx + 1 < COLS && grid[cy][cx+1] === target) stack.push([cx + 1, cy]);
            if (cx - 1 >= 0 && grid[cy][cx-1] === target) stack.push([cx - 1, cy]);
            if (cy + 1 < ROWS && grid[cy+1][cx] === target) stack.push([cx, cy + 1]);
            if (cy - 1 >= 0 && grid[cy-1][cx] === target) stack.push([cx, cy - 1]);
        }
    }
}

function encontrarEspacoVazioParaQix(qx, qy) {
    for (let i = -2; i <= 2; i++) {
        for (let j = -2; j <= 2; j++) {
            let nx = qx + i, ny = qy + j;
            if (grid[ny] && grid[ny][nx] === 0) {
                floodFill(nx, ny, 0, 4);
                return;
            }
        }
    }
}

// --- RESTANTE DA LÓGICA ---

function update() {
    if (gameState !== "PLAYING") return;
    if (player.invencivel) { player.blink++; if (player.blink > 100) player.invencivel = false; }
    
    // QIX
    qix.x += qix.vx; qix.y += qix.vy; qix.angle += qix.spin;
    if (qix.x < 25 || qix.x > canvas.width-25) qix.vx *= -1;
    if (qix.y < 25 || qix.y > canvas.height-25) qix.vy *= -1;

    // SPARX
    sparx.forEach(s => {
        let gX = Math.floor(s.x/cellW), gY = Math.floor(s.y/cellH);
        let nx = gX, ny = gY;
        if (s.dir === 'right') nx++; else if (s.dir === 'left') nx--; else if (s.dir === 'up') ny--; else if (s.dir === 'down') ny++;

        if (!grid[ny] || (grid[ny][nx] !== 1 && grid[ny][nx] !== 3) || grid[ny][nx] === 2) {
            const dirs = ['right', 'left', 'up', 'down'];
            for (let d of dirs) {
                let tx = gX, ty = gY;
                if (d === 'right') tx++; else if (d === 'left') tx--; else if (d === 'up') ty--; else if (d === 'down') ty++;
                if (grid[ty] && (grid[ty][tx] === 1 || grid[ty][tx] === 3) && grid[ty][tx] !== 2 && d !== getOpposite(s.dir)) {
                    s.dir = d; break;
                }
            }
        }
        if (s.dir === 'right') s.x += s.speed; else if (s.dir === 'left') s.x -= s.speed; else if (s.dir === 'up') s.y -= s.speed; else if (s.dir === 'down') s.y += s.speed;
        if (!player.invencivel && Math.abs(s.x - player.x) < 12 && Math.abs(s.y - player.y) < 12) startDeath();
    });

    // MOVIMENTO PLAYER
    let nX = player.x, nY = player.y, mov = false;
    if (keys['ArrowUp']) { nY -= player.speed; mov = true; }
    else if (keys['ArrowDown']) { nY += player.speed; mov = true; }
    else if (keys['ArrowLeft']) { nX -= player.speed; mov = true; }
    else if (keys['ArrowRight']) { nX += player.speed; mov = true; }
    
    if (mov) {
        let gX = Math.max(0, Math.min(COLS-1, Math.floor(nX/cellW)));
        let gY = Math.max(0, Math.min(ROWS-1, Math.floor(nY/cellH)));
        
        if (keys['Space']) {
            player.x = nX; player.y = nY;
            if (grid[gY][gX] === 0) { grid[gY][gX] = 2; player.isDrawing = true; }
            else if ((grid[gY][gX] === 1 || grid[gY][gX] === 3) && player.isDrawing) finalizeCut();
        } else if (grid[gY][gX] === 1 || grid[gY][gX] === 3) {
            player.x = nX; player.y = nY; player.isDrawing = false;
        }
    }
}

function draw() {
    ctx.fillStyle = CORES.FUNDO;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Scanlines
    ctx.fillStyle = "rgba(0, 0, 0, 0.2)";
    for(let i=0; i<canvas.height; i+=4) ctx.fillRect(0, i, canvas.width, 1);

    if (gameState === "START_MENU") drawOverlay("QIX TIME ATTACK", "Preencha a área sem ser tocado!");
    else if (gameState === "RANKING_VIEW") drawRanking();
    else if (gameState === "GAME_WIN") drawOverlay("VITÓRIA!", `Tempo: ${finalTimeStr}`);
    else if (gameState === "DYING") drawDeathEffect();
    else {
        for(let r=0; r<ROWS; r++) {
            for(let c=0; c<COLS; c++) {
                if (grid[r][c] === 1) ctx.fillStyle = CORES.LINHAS;
                else if (grid[r][c] === 2) ctx.fillStyle = CORES.MORTE;
                else if (grid[r][c] === 3) ctx.fillStyle = CORES.AREA;
                else continue;
                ctx.fillRect(c*cellW, r*cellH, cellW + 0.5, cellH + 0.5);
            }
        }
        // Qix
        ctx.strokeStyle = "#FF0"; ctx.lineWidth = 4; ctx.beginPath();
        ctx.moveTo(qix.x + Math.cos(qix.angle)*30, qix.y + Math.sin(qix.angle)*30);
        ctx.lineTo(qix.x - Math.cos(qix.angle)*30, qix.y - Math.sin(qix.angle)*30); ctx.stroke();
        // Sparx
        sparx.forEach(s => { ctx.fillStyle = CORES.SPARX; ctx.beginPath(); ctx.arc(s.x, s.y, 7, 0, Math.PI*2); ctx.fill(); });
        // Player
        if (!player.invencivel || Math.floor(Date.now()/100)%2===0) {
            ctx.fillStyle = CORES.PLAYER; ctx.fillRect(player.x-6, player.y-6, 12, 12);
        }
        drawHUD();
        if (gameState === "INPUT_NAME") drawInput();
    }
    requestAnimationFrame(draw);
}

function drawHUD() {
    ctx.fillStyle = "rgba(0,0,0,0.7)"; ctx.fillRect(0,0,canvas.width,35);
    ctx.fillStyle = "#FFF"; ctx.font = "bold 14px 'Courier New'"; ctx.textAlign = "left";
    ctx.fillText(`VIDAS: ${player.lives} | ÁREA: ${areaConquistada}% / ${metaArea}%`, 20, 22);
    ctx.textAlign = "right"; ctx.fillText(formatTime(performance.now()-startTime), canvas.width-20, 22);
}

function drawOverlay(t, s) {
    ctx.textAlign = "center"; ctx.fillStyle = CORES.PLAYER; ctx.font = "bold 45px 'Courier New'";
    ctx.fillText(t, canvas.width/2, canvas.height/3);
    ctx.fillStyle = "#FFF"; ctx.font = "18px 'Courier New'"; ctx.fillText(s, canvas.width/2, canvas.height/3 + 50);
    ["INICIAR CORRIDA", "RANKING"].forEach((txt, i) => {
        ctx.fillStyle = menuIndex === i ? CORES.PLAYER : "#777";
        ctx.fillText(`${menuIndex === i ? "> " : ""}${txt}`, canvas.width/2, canvas.height/2 + (i*60));
    });
}

function drawRanking() {
    ctx.textAlign = "center"; ctx.fillStyle = CORES.PLAYER; ctx.font = "28px 'Courier New'";
    ctx.fillText("RANKING DOS MELHORES", canvas.width/2, 80);
    let rk = JSON.parse(fs.readFileSync(rankingPath)).slice(0, 10);
    rk.forEach((item, i) => {
        ctx.fillStyle = "#FFF"; ctx.font = "16px 'Courier New'";
        ctx.fillText(`${i+1}. ${item.nome.padEnd(12,'.')} ${item.tempo}`, canvas.width/2, 140 + (i*25));
    });
    ctx.fillStyle = CORES.PLAYER; ctx.fillText("> VOLTAR", canvas.width/2, canvas.height - 50);
}

function drawInput() {
    ctx.fillStyle = "rgba(0,0,0,0.9)"; ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.textAlign = "center"; ctx.fillStyle = CORES.PLAYER; ctx.font = "22px 'Courier New'";
    ctx.fillText("DIGITE SEU NOME:", canvas.width/2, canvas.height/2 - 20);
    ctx.font = "45px 'Courier New'"; ctx.fillText(nomePlayer + "_", canvas.width/2, canvas.height/2 + 50);
}

function drawDeathEffect() {
    ctx.fillStyle = "#000";
    let h = (player.blink / 60) * canvas.height;
    ctx.fillRect(0, 0, canvas.width, h);
    player.blink++;
    if (player.blink > 60) {
        player.lives--;
        if (player.lives <= 0) { gameState = "START_MENU"; menuIndex = 0; }
        else { 
            player.x = 0; player.y = 0; player.invencivel = true; player.blink = 0; 
            replaceValueInGrid(2, 0); qix.x = canvas.width/2; qix.y = canvas.height/2;
            gameState = "PLAYING"; 
        }
    }
}

function calculateArea() {
    let p = 0;
    for (let r=1; r<ROWS-1; r++) for (let c=1; c<COLS-1; c++) if (grid[r][c] === 3) p++;
    areaConquistada = Math.floor((p / ((ROWS-2)*(COLS-2))) * 100);
    if (areaConquistada >= metaArea) { finalTimeStr = formatTime(performance.now()-startTime); gameState = "INPUT_NAME"; }
}

function startDeath() { if(gameState === "PLAYING") { gameState = "DYING"; player.blink = 0; } }
function replaceValueInGrid(o,n) { for(let r=0;r<ROWS;r++) for(let c=0;c<COLS;c++) if(grid[r][c]===o) grid[r][c]=n; }
function getOpposite(d) { return {right:'left', left:'right', up:'down', down:'up'}[d]; }
function formatTime(ms) {
    let t = Math.max(0, ms), min = Math.floor(t/60000).toString().padStart(2,'0');
    let sec = Math.floor((t%60000)/1000).toString().padStart(2,'0'), mil = Math.floor((t%1000)/10).toString().padStart(2,'0');
    return `${min}:${sec}:${mil}`;
}
function salvarRecorde() {
    let rk = JSON.parse(fs.readFileSync(rankingPath));
    rk.push({ nome: nomePlayer, tempo: finalTimeStr, ms: performance.now()-startTime });
    rk.sort((a,b) => a.ms - b.ms);
    fs.writeFileSync(rankingPath, JSON.stringify(rk.slice(0,10), null, 2));
    gameState = "GAME_WIN"; menuIndex = 0; nomePlayer = "";
}

draw();