// Barcode Scanner Integration

class BarcodeScanner {
    constructor() {
        this.scannerConfig = {
            prefix: '',
            suffix: '',
            minLength: 6,
            timeout: 100
        };
        this.scanBuffer = '';
        this.scanTimeout = null;
        this.isScanning = false;
        this.callbacks = new Map();
        
        this.init();
    }
    
    init() {
        // Load scanner configuration from localStorage
        const savedConfig = localStorage.getItem('barcode_scanner_config');
        if (savedConfig) {
            this.scannerConfig = { ...this.scannerConfig, ...JSON.parse(savedConfig) };
        }
        
        // Set up global keyboard listener for scanner input
        document.addEventListener('keydown', this.handleGlobalKeydown.bind(this));
    }
    
    updateConfig(config) {
        this.scannerConfig = { ...this.scannerConfig, ...config };
        localStorage.setItem('barcode_scanner_config', JSON.stringify(this.scannerConfig));
    }
    
    handleGlobalKeydown(event) {
        // Only process if no input field is focused (except our scanner fields)
        const activeElement = document.activeElement;
        const isScannerField = activeElement && activeElement.dataset.barcodeScanner === 'true';
        const isInputField = activeElement && (
            activeElement.tagName === 'INPUT' || 
            activeElement.tagName === 'TEXTAREA' || 
            activeElement.isContentEditable
        );
        
        if (!isScannerField && isInputField) {
            return;
        }
        
        // Handle barcode scanner input
        if (this.isValidScannerInput(event)) {
            event.preventDefault();
            this.handleScannerInput(event.key, activeElement);
        }
    }
    
    isValidScannerInput(event) {
        // Ignore modifier keys
        if (event.ctrlKey || event.altKey || event.metaKey) {
            return false;
        }
        
        // Allow numbers, letters, and some special characters
        return /^[a-zA-Z0-9\-_.]$/.test(event.key);
    }
    
    handleScannerInput(char, targetElement) {
        // Clear previous timeout
        if (this.scanTimeout) {
            clearTimeout(this.scanTimeout);
        }
        
        // Add character to buffer
        this.scanBuffer += char;
        this.isScanning = true;
        
        // Set timeout to process the scan
        this.scanTimeout = setTimeout(() => {
            this.processScan(targetElement);
        }, this.scannerConfig.timeout);
    }
    
    processScan(targetElement) {
        if (this.scanBuffer.length < this.scannerConfig.minLength) {
            this.resetScan();
            return;
        }
        
        let barcode = this.scanBuffer;
        
        // Remove prefix and suffix if configured
        if (this.scannerConfig.prefix && barcode.startsWith(this.scannerConfig.prefix)) {
            barcode = barcode.substring(this.scannerConfig.prefix.length);
        }
        
        if (this.scannerConfig.suffix && barcode.endsWith(this.scannerConfig.suffix)) {
            barcode = barcode.substring(0, barcode.length - this.scannerConfig.suffix.length);
        }
        
        // Trigger scan event
        this.triggerScan(barcode, targetElement);
        this.resetScan();
    }
    
    triggerScan(barcode, targetElement) {
        // Show barcode scan feedback to user
        const scanMessage = `Barcode Scanned: ${barcode}\n\nSearching for product in inventory...`;
        
        // Visual feedback
        this.showScanFeedback(targetElement, true);
        
        // If we have a specific target element with a callback
        if (targetElement && this.callbacks.has(targetElement)) {
            const callback = this.callbacks.get(targetElement);
            window.alert(scanMessage);
            callback(barcode);
            return;
        }
        
        // Default behavior - search for product
        if (window.pos) {
            window.alert(scanMessage);
            window.pos.searchByBarcode(barcode);
        } else {
            // For non-POS pages, fill the active field
            if (targetElement && (targetElement.tagName === 'INPUT' || targetElement.tagName === 'TEXTAREA')) {
                window.alert(`Barcode entered: ${barcode}`);
                targetElement.value = barcode;
                targetElement.dispatchEvent(new Event('input', { bubbles: true }));
            } else {
                window.alert(`Barcode scanned: ${barcode}\n\nNo active input field found. Please click on the barcode field first.`);
            }
        }
        
        // Play success sound
        this.playSuccessSound();
    }
    
    resetScan() {
        this.scanBuffer = '';
        this.isScanning = false;
        if (this.scanTimeout) {
            clearTimeout(this.scanTimeout);
            this.scanTimeout = null;
        }
    }
    
    showScanFeedback(element, success) {
        if (!element) return;
        
        const className = success ? 'scanner-success' : 'scanner-error';
        element.classList.add(className);
        
        setTimeout(() => {
            element.classList.remove(className);
        }, 1000);
    }
    
    playSuccessSound() {
        try {
            const audio = document.getElementById('scanSuccessSound');
            if (audio) {
                audio.currentTime = 0;
                audio.play().catch(e => console.log('Could not play sound:', e));
            }
        } catch (error) {
            console.log('Sound not available');
        }
    }
    
    registerCallback(element, callback) {
        if (element) {
            this.callbacks.set(element, callback);
            element.dataset.barcodeScanner = 'true';
        }
    }
    
    unregisterCallback(element) {
        if (element) {
            this.callbacks.delete(element);
            delete element.dataset.barcodeScanner;
        }
    }
}

// Global barcode scanner instance
window.barcodeScanner = new BarcodeScanner();

// Utility functions
function initBarcodeScanner(elementId, callback) {
    const element = document.getElementById(elementId);
    if (element) {
        element.dataset.barcodeScanner = 'true';
        element.placeholder = element.placeholder || 'Scan barcode or type to search...';
        
        if (callback) {
            window.barcodeScanner.registerCallback(element, callback);
        }
        
        // Add visual indicator
        element.addEventListener('focus', function() {
            this.classList.add('scanner-ready');
        });
        
        element.addEventListener('blur', function() {
            this.classList.remove('scanner-ready');
        });
    }
}

function initPOSBarcodeScanning() {
    // Set up global barcode scanning for POS interface
    document.body.dataset.barcodeScanner = 'true';
}

// Scanner configuration functions
function updateScannerConfig(config) {
    if (window.barcodeScanner) {
        window.barcodeScanner.updateConfig(config);
    }
}

function getScannerConfig() {
    return window.barcodeScanner ? window.barcodeScanner.scannerConfig : {};
}

// Test scanner function
function testBarcode(barcode) {
    if (window.barcodeScanner) {
        window.barcodeScanner.triggerScan(barcode, document.activeElement);
    }
}

// Export for modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BarcodeScanner, initBarcodeScanner, initPOSBarcodeScanning };
}
