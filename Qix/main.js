const { app, BrowserWindow } = require('electron');

function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    resizable: false, // Mantém o tamanho fixo como nos arcades
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  win.loadFile('index.html');
}

app.whenReady().then(createWindow);

// Fecha o app quando todas as janelas forem fechadas (padrão Linux/Windows)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});