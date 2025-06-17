// Main JavaScript for Comolor POS

// Global utility functions and common functionality
const ComolorPOS = {
    // Configuration
    config: {
        autoSaveInterval: 30000, // 30 seconds
        notificationTimeout: 5000,
        searchDebounceTime: 300
    },
    
    // Initialize the application
    init() {
        this.setupGlobalEventListeners();
        this.initializeTooltips();
        this.setupAutoSave();
        this.setupTheme();
        this.setupOfflineDetection();
        
        console.log('Comolor POS initialized');
    },
    
    // Set up global event listeners
    setupGlobalEventListeners() {
        // Note: Form and link handling is now managed by prompt-navigation.js
        
        // Handle AJAX errors
        document.addEventListener('ajaxError', this.handleAjaxError.bind(this));
        
        // Handle keyboard shortcuts
        document.addEventListener('keydown', this.handleGlobalKeyboard.bind(this));
        
        // Handle click outside to close dropdowns
        document.addEventListener('click', this.handleClickOutside.bind(this));
    },
    
    // Initialize Bootstrap tooltips
    initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },
    
    // Setup auto-save functionality
    setupAutoSave() {
        const forms = document.querySelectorAll('[data-auto-save]');
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('input', this.debounce(() => {
                    this.autoSaveForm(form);
                }, this.config.autoSaveInterval));
            });
        });
    },
    
    // Auto-save form data
    autoSaveForm(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        const formId = form.id || 'default';
        
        localStorage.setItem(`autosave_${formId}`, JSON.stringify({
            data: data,
            timestamp: Date.now()
        }));
        
        this.showNotification('Draft saved', 'info', 2000);
    },
    
    // Restore auto-saved data
    restoreAutoSave(formId) {
        const saved = localStorage.getItem(`autosave_${formId}`);
        if (saved) {
            const { data, timestamp } = JSON.parse(saved);
            
            // Only restore if less than 24 hours old
            if (Date.now() - timestamp < 24 * 60 * 60 * 1000) {
                return data;
            } else {
                localStorage.removeItem(`autosave_${formId}`);
            }
        }
        return null;
    },
    
    // Theme management
    setupTheme() {
        const savedTheme = localStorage.getItem('comolor_theme') || 'light';
        this.applyTheme(savedTheme);
        
        // Listen for theme changes
        document.addEventListener('themeChange', (event) => {
            this.applyTheme(event.detail.theme);
        });
    },
    
    applyTheme(theme) {
        document.body.className = document.body.className.replace(/theme-\w+/g, '');
        document.body.classList.add(`theme-${theme}`);
        localStorage.setItem('comolor_theme', theme);
        
        // Update theme color meta tag
        const themeColor = theme === 'dark' ? '#1a202c' : '#ffffff';
        let metaTheme = document.querySelector('meta[name="theme-color"]');
        if (!metaTheme) {
            metaTheme = document.createElement('meta');
            metaTheme.name = 'theme-color';
            document.head.appendChild(metaTheme);
        }
        metaTheme.content = themeColor;
    },
    
    // Offline detection
    setupOfflineDetection() {
        window.addEventListener('online', () => {
            this.showNotification('Connection restored', 'success');
            this.syncOfflineData();
        });
        
        window.addEventListener('offline', () => {
            this.showNotification('Working offline', 'warning');
        });
    },
    
    // Sync offline data when connection is restored
    async syncOfflineData() {
        const offlineData = this.getOfflineData();
        if (offlineData.length > 0) {
            try {
                for (const item of offlineData) {
                    await this.syncDataItem(item);
                }
                this.clearOfflineData();
                this.showNotification('Offline data synced', 'success');
            } catch (error) {
                console.error('Error syncing offline data:', error);
                this.showNotification('Sync failed. Will retry later.', 'warning');
            }
        }
    },
    
    // Note: Form and link handling is now managed by the comprehensive prompt-navigation.js system
    
    // Handle global keyboard shortcuts
    handleGlobalKeyboard(event) {
        // Ctrl/Cmd + K for global search
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            const searchField = document.querySelector('[data-global-search]');
            if (searchField) {
                searchField.focus();
            }
        }
        
        // Escape to close modals and dropdowns
        if (event.key === 'Escape') {
            // Close any open modals
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            });
            
            // Close any open dropdowns
            const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
            openDropdowns.forEach(dropdown => {
                const toggle = dropdown.previousElementSibling;
                if (toggle) toggle.click();
            });
        }
    },
    
    // Handle clicks outside elements
    handleClickOutside(event) {
        // Close custom dropdowns when clicking outside
        const customDropdowns = document.querySelectorAll('.custom-dropdown.show');
        customDropdowns.forEach(dropdown => {
            if (!dropdown.contains(event.target)) {
                dropdown.classList.remove('show');
            }
        });
    },
    
    // Show notification
    showNotification(message, type = 'info', duration = null) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${this.getBootstrapAlertClass(type)} alert-dismissible fade show position-fixed notification`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 500px;';
        
        const icon = this.getNotificationIcon(type);
        notification.innerHTML = `
            <i data-feather="${icon}" class="me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        feather.replace();
        
        // Auto-remove
        const timeout = duration || this.config.notificationTimeout;
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 150);
            }
        }, timeout);
        
        return notification;
    },
    
    // Get Bootstrap alert class for notification type
    getBootstrapAlertClass(type) {
        const mapping = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return mapping[type] || 'info';
    },
    
    // Get icon for notification type
    getNotificationIcon(type) {
        const mapping = {
            'success': 'check-circle',
            'error': 'x-circle',
            'warning': 'alert-triangle',
            'info': 'info'
        };
        return mapping[type] || 'info';
    },
    
    // Set button loading state
    setButtonLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
        } else {
            button.disabled = false;
            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText;
                delete button.dataset.originalText;
            }
        }
    },
    
    // Debounce function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Format currency
    formatCurrency(amount, currency = 'KES') {
        return new Intl.NumberFormat('en-KE', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        }).format(amount);
    },
    
    // Format date
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        return new Intl.DateTimeFormat('en-KE', { ...defaultOptions, ...options }).format(new Date(date));
    },
    
    // Validate form
    validateForm(form) {
        const errors = [];
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                errors.push(`${field.labels[0]?.textContent || field.name} is required`);
                field.classList.add('is-invalid');
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        // Email validation
        const emailFields = form.querySelectorAll('input[type="email"]');
        emailFields.forEach(field => {
            if (field.value && !this.isValidEmail(field.value)) {
                errors.push('Please enter a valid email address');
                field.classList.add('is-invalid');
            }
        });
        
        // Phone validation
        const phoneFields = form.querySelectorAll('input[type="tel"]');
        phoneFields.forEach(field => {
            if (field.value && !this.isValidPhone(field.value)) {
                errors.push('Please enter a valid phone number');
                field.classList.add('is-invalid');
            }
        });
        
        return errors;
    },
    
    // Email validation
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    // Phone validation (Kenyan format)
    isValidPhone(phone) {
        const phoneRegex = /^(\+254|0)[17]\d{8}$/;
        return phoneRegex.test(phone.replace(/\s/g, ''));
    },
    
    // Local storage helpers
    setLocalData(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Error saving to localStorage:', error);
            return false;
        }
    },
    
    getLocalData(key) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : null;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return null;
        }
    },
    
    // Offline data management
    addOfflineData(data) {
        const offlineData = this.getOfflineData();
        offlineData.push({
            ...data,
            timestamp: Date.now(),
            id: Date.now().toString()
        });
        this.setLocalData('offline_data', offlineData);
    },
    
    getOfflineData() {
        return this.getLocalData('offline_data') || [];
    },
    
    clearOfflineData() {
        localStorage.removeItem('offline_data');
    },
    
    // AJAX helpers
    async makeRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };
        
        try {
            const response = await fetch(url, defaultOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return { success: true, data };
        } catch (error) {
            console.error('Request failed:', error);
            
            // Store for offline sync if it's a POST/PUT/PATCH request
            if (['POST', 'PUT', 'PATCH'].includes(defaultOptions.method?.toUpperCase())) {
                this.addOfflineData({
                    url,
                    options: defaultOptions,
                    type: 'request'
                });
            }
            
            return { success: false, error: error.message };
        }
    },
    
    // Print helper
    printElement(elementId, title = 'Print') {
        const element = document.getElementById(elementId);
        if (!element) {
            window.alert('Print element not found: ' + elementId);
            return;
        }
        
        const content = element.innerText.substring(0, 500);
        window.alert('Print Preview - ' + title + ':\n\n' + content + (content.length >= 500 ? '\n\n[Content truncated...]' : ''));
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ComolorPOS.init();
    
    // Initialize any auto-save forms
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    autoSaveForms.forEach(form => {
        const savedData = ComolorPOS.restoreAutoSave(form.id);
        if (savedData) {
            // Show restore option
            const restoreBtn = document.createElement('button');
            restoreBtn.type = 'button';
            restoreBtn.className = 'btn btn-outline-info btn-sm mb-3';
            restoreBtn.innerHTML = '<i data-feather="rotate-ccw"></i> Restore draft';
            restoreBtn.onclick = () => {
                Object.entries(savedData).forEach(([name, value]) => {
                    const field = form.querySelector(`[name="${name}"]`);
                    if (field) field.value = value;
                });
                restoreBtn.remove();
                ComolorPOS.showNotification('Draft restored', 'success');
            };
            
            form.insertBefore(restoreBtn, form.firstChild);
            feather.replace();
        }
    });
});

// Export for global use
window.ComolorPOS = ComolorPOS;

// Service Worker registration for offline support
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}
