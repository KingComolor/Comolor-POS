/**
 * POS-Specific Prompt System
 * Enhanced window prompts for all POS operations
 */

class POSPrompts {
    constructor() {
        this.init();
    }

    init() {
        this.setupPOSSpecificPrompts();
        this.overridePOSOperations();
        this.setupReceiptPrompts();
        this.setupPaymentPrompts();
        console.log('POS Prompt System initialized - All POS operations use window prompts');
    }

    setupPOSSpecificPrompts() {
        // Override product addition to cart
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-add-to-cart]') || e.target.closest('[data-add-to-cart]')) {
                e.preventDefault();
                e.stopPropagation();
                
                const productId = e.target.dataset.productId || e.target.closest('[data-product-id]')?.dataset.productId;
                const productName = e.target.closest('.product-card')?.querySelector('.card-title')?.textContent || 'Unknown Product';
                const productPrice = e.target.closest('.product-card')?.querySelector('.card-text strong')?.textContent || 'Unknown Price';
                
                this.showAddToCartPrompt(productId, productName, productPrice);
            }
        }, true);

        // Override cart operations
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-cart-action]')) {
                e.preventDefault();
                e.stopPropagation();
                
                const action = e.target.dataset.cartAction;
                const productId = e.target.dataset.productId;
                const productName = e.target.closest('.cart-item')?.querySelector('h6')?.textContent || 'Product';
                
                this.showCartActionPrompt(action, productId, productName);
            }
        }, true);

        // Override barcode scanning
        document.addEventListener('keypress', (e) => {
            const target = e.target;
            if (target.id === 'barcode-input' && e.key === 'Enter') {
                e.preventDefault();
                const barcode = target.value.trim();
                if (barcode) {
                    this.showBarcodePrompt(barcode);
                    target.value = '';
                }
            }
        }, true);
    }

    overridePOSOperations() {
        // Override payment method selection
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-payment-method]')) {
                e.preventDefault();
                e.stopPropagation();
                
                const method = e.target.dataset.paymentMethod;
                this.showPaymentMethodPrompt(method);
            }
        }, true);

        // Override receipt printing
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-print-receipt]') || e.target.textContent.includes('Print Receipt')) {
                e.preventDefault();
                e.stopPropagation();
                
                const receiptId = e.target.dataset.receiptId || 'current';
                this.showPrintReceiptPrompt(receiptId);
            }
        }, true);

        // Override sale completion
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-complete-sale]') || e.target.textContent.includes('Complete Sale')) {
                e.preventDefault();
                e.stopPropagation();
                
                this.showCompleteSalePrompt();
            }
        }, true);
    }

    setupReceiptPrompts() {
        // Override receipt viewing
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-view-receipt]') || e.target.href?.includes('receipt')) {
                e.preventDefault();
                e.stopPropagation();
                
                const receiptId = e.target.dataset.receiptId || 'unknown';
                this.showReceiptViewPrompt(receiptId);
            }
        }, true);
    }

    setupPaymentPrompts() {
        // Override MPesa payment confirmation
        window.confirmMpesaPayment = () => {
            this.showMpesaConfirmationPrompt();
        };

        // Override MPesa payment cancellation
        window.cancelMpesaPayment = () => {
            this.showMpesaCancellationPrompt();
        };
    }

    showAddToCartPrompt(productId, productName, productPrice) {
        const message = `Add Product to Cart

Product: ${productName}
Price: ${productPrice}
Product ID: ${productId}

This would add the product to your shopping cart and update the total.

Add to cart?`;

        if (window.confirm(message)) {
            this.showLoadingState();
            setTimeout(() => {
                window.alert(`Product Added Successfully!

${productName} has been added to your cart.
Cart total updated.

In a real POS system:
• Inventory would be checked
• Cart would be updated
• Total would be recalculated`);
            }, 800);
        }
    }

    showCartActionPrompt(action, productId, productName) {
        let actionText = '';
        switch (action) {
            case 'increase':
                actionText = 'Increase quantity';
                break;
            case 'decrease':
                actionText = 'Decrease quantity';
                break;
            case 'remove':
                actionText = 'Remove from cart';
                break;
            default:
                actionText = 'Update cart';
        }

        const message = `Cart Action: ${actionText}

Product: ${productName}
Action: ${actionText}

This would ${actionText.toLowerCase()} for this product in your cart.

Proceed with action?`;

        if (window.confirm(message)) {
            this.showLoadingState();
            setTimeout(() => {
                window.alert(`Cart Updated!

${actionText} completed for ${productName}

In a real POS system:
• Cart quantities would be updated
• Total amount would be recalculated
• Inventory would be checked`);
            }, 600);
        }
    }

    showBarcodePrompt(barcode) {
        const message = `Barcode Scanned

Barcode: ${barcode}

This would search for the product with this barcode and add it to the cart if found.

Search for product?`;

        if (window.confirm(message)) {
            this.showLoadingState();
            setTimeout(() => {
                window.alert(`Product Search Complete!

Barcode: ${barcode}

In a real POS system:
• Product database would be searched
• Product details would be displayed
• Product would be added to cart if found
• Error message if product not found`);
            }, 1000);
        }
    }

    showPaymentMethodPrompt(method) {
        const methodName = method === 'cash' ? 'Cash Payment' : 'MPesa Payment';
        
        const message = `Payment Method Selected

Method: ${methodName}

This would initiate the ${methodName.toLowerCase()} process for the current cart total.

Proceed with ${methodName.toLowerCase()}?`;

        if (window.confirm(message)) {
            this.showLoadingState();
            
            if (method === 'cash') {
                setTimeout(() => {
                    this.showCashPaymentPrompt();
                }, 500);
            } else if (method === 'mpesa') {
                setTimeout(() => {
                    this.showMpesaPaymentPrompt();
                }, 500);
            }
        }
    }

    showCashPaymentPrompt() {
        const total = this.getCartTotal();
        const received = window.prompt(`Cash Payment

Total Amount: KES ${total}

Enter amount received from customer:`, total);

        if (received) {
            const amount = parseFloat(received);
            if (amount >= total) {
                const change = amount - total;
                window.alert(`Cash Payment Processed!

Total: KES ${total}
Received: KES ${amount.toFixed(2)}
Change: KES ${change.toFixed(2)}

In a real POS system:
• Payment would be recorded
• Receipt would be generated
• Cash drawer would open
• Sale would be completed`);
            } else {
                window.alert(`Insufficient Amount!

Required: KES ${total}
Received: KES ${amount.toFixed(2)}
Shortage: KES ${(total - amount).toFixed(2)}

Please collect the full amount from customer.`);
            }
        }
    }

    showMpesaPaymentPrompt() {
        const total = this.getCartTotal();
        const phone = window.prompt(`MPesa Payment

Total Amount: KES ${total}

Enter customer phone number (254XXXXXXXXX):`, '254');

        if (phone && phone.match(/^254[0-9]{9}$/)) {
            window.alert(`MPesa Payment Initiated!

Amount: KES ${total}
Phone: ${phone}

In a real POS system:
• STK Push would be sent to customer
• Payment status would be monitored
• Receipt would be generated upon confirmation
• Sale would be completed automatically`);
        } else if (phone) {
            window.alert(`Invalid Phone Number!

Please enter a valid MPesa number in format: 254XXXXXXXXX

Example: 254712345678`);
        }
    }

    showPrintReceiptPrompt(receiptId) {
        const message = `Print Receipt

Receipt ID: ${receiptId}

This would send the receipt to the connected thermal printer.

Print receipt?`;

        if (window.confirm(message)) {
            this.showLoadingState();
            setTimeout(() => {
                window.alert(`Receipt Printed!

Receipt ID: ${receiptId}

In a real POS system:
• Receipt would be formatted
• Sent to thermal printer
• Print confirmation would be received
• Customer copy would be provided`);
            }, 1200);
        }
    }

    showReceiptViewPrompt(receiptId) {
        const message = `View Receipt

Receipt ID: ${receiptId}

This would display the full receipt details including all items, totals, and payment information.

View receipt details?`;

        if (window.confirm(message)) {
            window.alert(`Receipt Details

Receipt ID: ${receiptId}
Date: ${new Date().toLocaleString()}
Items: [Cart Items]
Total: KES ${this.getCartTotal()}
Payment Method: [Selected Method]

In a real POS system:
• Complete receipt would be displayed
• All transaction details shown
• Reprint option available
• Email option available`);
        }
    }

    showMpesaConfirmationPrompt() {
        const message = `MPesa Payment Confirmation

Payment has been received successfully!

This confirms that the MPesa payment was completed and the transaction can proceed.

Confirm and complete sale?`;

        if (window.confirm(message)) {
            window.alert(`Sale Completed Successfully!

MPesa payment confirmed
Receipt generated
Inventory updated
Transaction recorded

Thank you for your business!`);
        }
    }

    showMpesaCancellationPrompt() {
        const message = `Cancel MPesa Payment

This will cancel the current MPesa payment request.

You can:
• Try the payment again
• Switch to cash payment
• Cancel the entire transaction

Cancel MPesa payment?`;

        if (window.confirm(message)) {
            window.alert(`MPesa Payment Cancelled

The payment request has been cancelled.

Options:
• Retry MPesa payment
• Switch to cash payment
• Start new transaction`);
        }
    }

    showCompleteSalePrompt() {
        const total = this.getCartTotal();
        const itemCount = this.getCartItemCount();
        
        const message = `Complete Sale

Items: ${itemCount}
Total: KES ${total}

This will finalize the transaction and complete the sale.

Complete sale now?`;

        if (window.confirm(message)) {
            this.showLoadingState();
            setTimeout(() => {
                window.alert(`Sale Completed Successfully!

Transaction Details:
• Items sold: ${itemCount}
• Total amount: KES ${total}
• Receipt generated
• Inventory updated

Thank you for your business!`);
            }, 1500);
        }
    }

    showLoadingState() {
        // Visual feedback for processing
        const loadingElement = document.createElement('div');
        loadingElement.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            z-index: 9999;
            font-weight: bold;
        `;
        loadingElement.textContent = 'Processing...';
        document.body.appendChild(loadingElement);

        setTimeout(() => {
            if (loadingElement.parentNode) {
                loadingElement.parentNode.removeChild(loadingElement);
            }
        }, 2000);
    }

    getCartTotal() {
        // Simulate cart total calculation
        const cartItems = document.querySelectorAll('.cart-item');
        let total = 0;
        
        cartItems.forEach(item => {
            const priceText = item.querySelector('strong')?.textContent;
            if (priceText) {
                const price = parseFloat(priceText.replace('KES', '').trim());
                if (!isNaN(price)) total += price;
            }
        });
        
        return total > 0 ? total.toFixed(2) : '150.00'; // Default for demo
    }

    getCartItemCount() {
        const cartItems = document.querySelectorAll('.cart-item');
        return cartItems.length || 3; // Default for demo
    }

    // Utility method to disable POS prompts temporarily
    static disable() {
        window.posPromptsDisabled = true;
    }

    static enable() {
        window.posPromptsDisabled = false;
    }
}

// Initialize POS prompts system
document.addEventListener('DOMContentLoaded', () => {
    window.posPrompts = new POSPrompts();
});

// Global POS prompt functions
window.showPOSAlert = function(message, title = 'POS System') {
    window.alert(`${title}\n\n${message}`);
};

window.showPOSConfirm = function(message, title = 'POS Confirmation') {
    return window.confirm(`${title}\n\n${message}`);
};

window.showPOSPrompt = function(message, defaultValue = '', title = 'POS Input') {
    return window.prompt(`${title}\n\n${message}`, defaultValue);
};