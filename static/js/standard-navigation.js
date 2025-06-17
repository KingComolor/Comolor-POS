/**
 * Standard Navigation System
 * Enables proper server-side navigation without embedded page handling
 */

class StandardNavigation {
    constructor() {
        this.init();
    }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupNavigation());
        } else {
            this.setupNavigation();
        }
    }

    setupNavigation() {
        this.enableFormConfirmations();
        this.enableDeleteConfirmations();
        this.setupFormValidation();
        console.log('Standard server-side navigation enabled');
    }

    enableFormConfirmations() {
        // Add confirmation dialogs for dangerous actions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            const action = form.action || '';
            
            if (action.includes('/delete') || form.dataset.confirm) {
                const message = form.dataset.confirmMessage || 'Are you sure you want to delete this item?';
                if (!confirm(message)) {
                    e.preventDefault();
                }
            }
        });
    }

    enableDeleteConfirmations() {
        // Add confirmation for delete links
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (!link) return;

            const href = link.getAttribute('href') || '';
            
            if (href.includes('/delete') || link.classList.contains('delete-action')) {
                const itemName = link.dataset.itemName || 'this item';
                if (!confirm(`Are you sure you want to delete ${itemName}?`)) {
                    e.preventDefault();
                }
            }
        });
    }

    setupFormValidation() {
        // Basic client-side validation helpers
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const requiredFields = form.querySelectorAll('[required]');
                let isValid = true;

                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        field.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        field.classList.remove('is-invalid');
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                    alert('Please fill in all required fields.');
                }
            });
        });
    }
}

// Initialize standard navigation
window.standardNavigation = new StandardNavigation();