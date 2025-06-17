# Desktop App Packaging Guide for Comolor POS

## Overview

This guide covers converting the Comolor POS web application into a desktop application using Electron and Tauri frameworks, with options for Windows, macOS, and Linux distribution.

## Desktop App Architecture

### Technology Options

1. **Electron** (Recommended for rapid development)
   - Uses Chromium and Node.js
   - Cross-platform compatibility
   - Larger file size but easier development

2. **Tauri** (Recommended for production)
   - Uses system webview and Rust backend
   - Smaller file size and better performance
   - More secure with restricted API access

3. **Progressive Web App (PWA)**
   - Web-based but installable
   - Smallest footprint
   - Limited offline capabilities

## Option 1: Electron Desktop App

### 1. Project Setup

Create desktop app structure:
```bash
mkdir comolor-pos-desktop
cd comolor-pos-desktop
npm init -y
```

### 2. Install Dependencies

```bash
# Core Electron dependencies
npm install --save-dev electron
npm install --save-dev electron-builder
npm install --save-dev electron-packager

# Additional utilities
npm install --save electron-updater
npm install --save electron-store
npm install --save node-fetch
```

### 3. Create Main Process (main.js)

```javascript
const { app, BrowserWindow, Menu, ipcMain, shell } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const { autoUpdater } = require('electron-updater');
const Store = require('electron-store');

// Initialize settings store
const store = new Store();

let mainWindow;

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 1000,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets/icon.png'),
    title: 'Comolor POS System',
    show: false
  });

  // Load the web application
  const serverUrl = store.get('serverUrl', 'https://your-app.onrender.com');
  mainWindow.loadURL(serverUrl);

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Focus on window (optional)
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// App event listeners
app.whenReady().then(() => {
  createWindow();
  createMenu();
  
  // Check for updates (production only)
  if (!isDev) {
    autoUpdater.checkForUpdatesAndNotify();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Create application menu
function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Settings',
          click: () => {
            createSettingsWindow();
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About Comolor POS',
          click: () => {
            require('electron').dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Comolor POS',
              message: 'Comolor POS System',
              detail: 'Version 1.0.0\nPoint of Sale system for Kenyan retailers'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Settings window
function createSettingsWindow() {
  const settingsWindow = new BrowserWindow({
    width: 500,
    height: 400,
    parent: mainWindow,
    modal: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  settingsWindow.loadFile('settings.html');
}

// IPC handlers
ipcMain.handle('get-server-url', () => {
  return store.get('serverUrl', 'https://your-app.onrender.com');
});

ipcMain.handle('set-server-url', (event, url) => {
  store.set('serverUrl', url);
  return true;
});

ipcMain.handle('restart-app', () => {
  app.relaunch();
  app.exit();
});

// Auto-updater events
autoUpdater.on('checking-for-update', () => {
  console.log('Checking for update...');
});

autoUpdater.on('update-available', (info) => {
  console.log('Update available.');
});

autoUpdater.on('update-not-available', (info) => {
  console.log('Update not available.');
});

autoUpdater.on('error', (err) => {
  console.log('Error in auto-updater. ' + err);
});
```

### 4. Create Preload Script (preload.js)

```javascript
const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  getServerUrl: () => ipcRenderer.invoke('get-server-url'),
  setServerUrl: (url) => ipcRenderer.invoke('set-server-url', url),
  restartApp: () => ipcRenderer.invoke('restart-app'),
  
  // Barcode scanner integration
  onBarcodeScanned: (callback) => {
    ipcRenderer.on('barcode-scanned', callback);
  },
  
  // Printer integration
  printReceipt: (receiptData) => {
    return ipcRenderer.invoke('print-receipt', receiptData);
  },
  
  // System info
  getSystemInfo: () => ipcRenderer.invoke('get-system-info')
});
```

### 5. Create Settings Page (settings.html)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Comolor POS Settings</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="url"] {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background: #5a6fd8;
        }
    </style>
</head>
<body>
    <h2>POS Settings</h2>
    
    <form id="settings-form">
        <div class="form-group">
            <label for="server-url">Server URL:</label>
            <input type="url" id="server-url" placeholder="https://your-app.onrender.com" required>
        </div>
        
        <button type="submit">Save Settings</button>
        <button type="button" id="restart-btn">Save & Restart</button>
    </form>

    <script>
        // Load current settings
        window.electronAPI.getServerUrl().then(url => {
            document.getElementById('server-url').value = url;
        });

        // Handle form submission
        document.getElementById('settings-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = document.getElementById('server-url').value;
            await window.electronAPI.setServerUrl(url);
            alert('Settings saved!');
        });

        // Handle restart
        document.getElementById('restart-btn').addEventListener('click', async () => {
            const url = document.getElementById('server-url').value;
            await window.electronAPI.setServerUrl(url);
            window.electronAPI.restartApp();
        });
    </script>
</body>
</html>
```

### 6. Update package.json

```json
{
  "name": "comolor-pos-desktop",
  "version": "1.0.0",
  "description": "Comolor POS Desktop Application",
  "main": "main.js",
  "homepage": "./",
  "scripts": {
    "start": "electron .",
    "dev": "electron . --dev",
    "build": "electron-builder",
    "build-win": "electron-builder --win",
    "build-mac": "electron-builder --mac",
    "build-linux": "electron-builder --linux",
    "dist": "electron-builder --publish=never"
  },
  "build": {
    "appId": "com.comolor.pos",
    "productName": "Comolor POS",
    "directories": {
      "output": "dist"
    },
    "files": [
      "main.js",
      "preload.js",
      "settings.html",
      "assets/**/*",
      "node_modules/**/*"
    ],
    "win": {
      "target": "nsis",
      "icon": "assets/icon.ico"
    },
    "mac": {
      "target": "dmg",
      "icon": "assets/icon.icns",
      "category": "public.app-category.business"
    },
    "linux": {
      "target": "AppImage",
      "icon": "assets/icon.png",
      "category": "Office"
    },
    "publish": {
      "provider": "github",
      "owner": "your-username",
      "repo": "comolor-pos-desktop"
    }
  },
  "author": "Your Company",
  "license": "MIT"
}
```

### 7. Build Desktop App

```bash
# Development
npm run dev

# Build for current platform
npm run build

# Build for specific platforms
npm run build-win    # Windows
npm run build-mac    # macOS
npm run build-linux  # Linux

# Build for all platforms
npm run dist
```

## Option 2: Tauri Desktop App

### 1. Install Rust and Tauri CLI

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Tauri CLI
cargo install tauri-cli
```

### 2. Create Tauri Project

```bash
npm create tauri-app@latest comolor-pos-tauri
cd comolor-pos-tauri
```

### 3. Configure Tauri (tauri.conf.json)

```json
{
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devPath": "http://localhost:1420",
    "distDir": "../dist"
  },
  "package": {
    "productName": "Comolor POS",
    "version": "1.0.0"
  },
  "tauri": {
    "allowlist": {
      "all": false,
      "shell": {
        "all": false,
        "open": true
      },
      "http": {
        "all": true,
        "request": true
      },
      "fs": {
        "all": false,
        "readFile": true,
        "writeFile": true,
        "exists": true
      }
    },
    "bundle": {
      "active": true,
      "targets": "all",
      "identifier": "com.comolor.pos",
      "icon": [
        "icons/32x32.png",
        "icons/128x128.png",
        "icons/128x128@2x.png",
        "icons/icon.icns",
        "icons/icon.ico"
      ]
    },
    "security": {
      "csp": null
    },
    "windows": [
      {
        "fullscreen": false,
        "resizable": true,
        "title": "Comolor POS",
        "width": 1200,
        "height": 800,
        "minWidth": 1000,
        "minHeight": 700
      }
    ]
  }
}
```

### 4. Build Tauri App

```bash
# Development
npm run tauri dev

# Build for production
npm run tauri build
```

## Option 3: Progressive Web App (PWA)

### 1. Add PWA Manifest

Create `static/manifest.json`:
```json
{
  "name": "Comolor POS System",
  "short_name": "Comolor POS",
  "description": "Point of Sale system for Kenyan retailers",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#667eea",
  "icons": [
    {
      "src": "/static/images/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/images/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### 2. Add Service Worker

Create `static/sw.js`:
```javascript
const CACHE_NAME = 'comolor-pos-v1';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/pos.js',
  '/static/images/logo.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});
```

### 3. Register Service Worker

Add to your base template:
```html
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then((registration) => {
        console.log('SW registered: ', registration);
      })
      .catch((registrationError) => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}
</script>
```

## Hardware Integration

### Barcode Scanner Integration

#### For Electron:
```javascript
// In main.js
const { ipcMain } = require('electron');
const { spawn } = require('child_process');

// USB barcode scanner listener
ipcMain.handle('start-barcode-scanner', () => {
  // This depends on your specific barcode scanner
  // Most USB scanners work as keyboard input
  return true;
});

// Handle keyboard input for barcode scanning
mainWindow.webContents.on('before-input-event', (event, input) => {
  if (input.type === 'keyDown' && input.key === 'Enter') {
    // Check if this is from barcode scanner
    // Send to renderer process
    mainWindow.webContents.send('barcode-scanned', barcodeData);
  }
});
```

#### For Web (PWA):
```javascript
// Barcode scanner via camera
async function startBarcodeScanner() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      video: { facingMode: 'environment' } 
    });
    // Use a barcode scanning library like ZXing
    // Process camera stream for barcodes
  } catch (err) {
    console.error('Camera access denied:', err);
  }
}
```

### Receipt Printer Integration

#### For Electron:
```javascript
// In main.js
const { ipcMain } = require('electron');
const printer = require('printer'); // npm install printer

ipcMain.handle('print-receipt', async (event, receiptData) => {
  try {
    const printers = printer.getPrinters();
    const defaultPrinter = printers.find(p => p.isDefault) || printers[0];
    
    if (!defaultPrinter) {
      throw new Error('No printer found');
    }
    
    // Format receipt data for thermal printer
    const printData = formatReceiptForPrinter(receiptData);
    
    printer.printDirect({
      data: printData,
      printer: defaultPrinter.name,
      type: 'RAW',
      success: () => console.log('Receipt printed successfully'),
      error: (err) => console.error('Print error:', err)
    });
    
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

function formatReceiptForPrinter(receiptData) {
  // Format receipt data for ESC/POS thermal printer
  let output = '';
  output += '\x1B\x40'; // Initialize printer
  output += '\x1B\x61\x01'; // Center align
  output += receiptData.shopName + '\n';
  output += receiptData.address + '\n';
  output += '--------------------------------\n';
  
  receiptData.items.forEach(item => {
    output += `${item.name.padEnd(20)} ${item.total.padStart(10)}\n`;
  });
  
  output += '--------------------------------\n';
  output += `TOTAL: ${receiptData.total.padStart(25)}\n`;
  output += '\x1B\x64\x05'; // Feed 5 lines
  output += '\x1D\x56\x42\x00'; // Cut paper
  
  return output;
}
```

## Distribution and Updates

### Electron Distribution

1. **Auto-updater Setup**
```javascript
const { autoUpdater } = require('electron-updater');

// Configure update server
autoUpdater.setFeedURL({
  provider: 'github',
  owner: 'your-username',
  repo: 'comolor-pos-desktop'
});

// Check for updates on app start
app.whenReady().then(() => {
  autoUpdater.checkForUpdatesAndNotify();
});
```

2. **Code Signing** (for production)
```bash
# Windows (requires certificate)
npm run build-win -- --publish=never

# macOS (requires Apple Developer account)
npm run build-mac -- --publish=never
```

### Distribution Channels

1. **GitHub Releases**
   - Automated with electron-builder
   - Free hosting
   - Manual download

2. **Microsoft Store** (Windows)
   - Requires Windows Developer account
   - Automated updates
   - Better user trust

3. **Mac App Store** (macOS)
   - Requires Apple Developer account
   - Strict review process
   - Sandboxed environment

4. **Snap Store** (Linux)
   - Easy distribution
   - Automatic updates
   - Cross-distribution compatibility

## Security Considerations

### Desktop App Security

1. **Context Isolation**
```javascript
// Always enable context isolation
webPreferences: {
  contextIsolation: true,
  nodeIntegration: false,
  enableRemoteModule: false
}
```

2. **Content Security Policy**
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';">
```

3. **Secure Communication**
```javascript
// Only allow HTTPS connections
const allowedHosts = ['your-app.onrender.com'];

mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
  const parsedUrl = new URL(navigationUrl);
  if (!allowedHosts.includes(parsedUrl.hostname)) {
    event.preventDefault();
  }
});
```

## Performance Optimization

### App Size Optimization

1. **Electron**
```json
// package.json build config
"build": {
  "compression": "maximum",
  "nsis": {
    "oneClick": false,
    "allowToChangeInstallationDirectory": true
  }
}
```

2. **Tauri**
```toml
# Cargo.toml
[profile.release]
lto = true
codegen-units = 1
panic = "abort"
```

### Runtime Performance

1. **Memory Management**
```javascript
// Clear cache periodically
setInterval(() => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.session.clearCache();
  }
}, 30 * 60 * 1000); // Every 30 minutes
```

2. **Background Tasks**
```javascript
// Use web workers for heavy tasks
const worker = new Worker('worker.js');
worker.postMessage(heavyTaskData);
```

## Testing and Quality Assurance

### Testing Framework

1. **Electron Testing**
```bash
npm install --save-dev spectron mocha
```

```javascript
// test.js
const { Application } = require('spectron');
const assert = require('assert');

describe('Application launch', function () {
  this.timeout(10000);

  beforeEach(function () {
    this.app = new Application({
      path: 'path/to/your/electron/binary'
    });
    return this.app.start();
  });

  afterEach(function () {
    if (this.app && this.app.isRunning()) {
      return this.app.stop();
    }
  });

  it('shows an initial window', function () {
    return this.app.client.getWindowCount().then(function (count) {
      assert.equal(count, 1);
    });
  });
});
```

### Cross-Platform Testing

1. **Virtual Machines**
   - Test on Windows, macOS, Linux
   - Different screen resolutions
   - Various hardware configurations

2. **Automated Testing**
   - GitHub Actions for CI/CD
   - Automated builds for all platforms
   - Integration testing

## Deployment Checklist

- [ ] App builds successfully on all target platforms
- [ ] Hardware integration (barcode scanner, printer) works
- [ ] Server connection configuration works
- [ ] Offline mode functionality (if implemented)
- [ ] Auto-update mechanism works
- [ ] App signing and notarization complete
- [ ] Installation packages tested
- [ ] User documentation created
- [ ] Support channels established

This comprehensive guide covers all aspects of packaging your Comolor POS system as a desktop application, from development to distribution.