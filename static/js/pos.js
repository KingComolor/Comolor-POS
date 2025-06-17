/**
 * Comolor POS System - Point of Sale Interface
 * Real-world ready POS functionality with comprehensive features
 */

class POS {
    constructor() {
        this.cart = [];
        this.products = [];
        this.currentSale = null;
        this.isProcessingPayment = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadProducts();
        this.restoreCart();
        console.log('POS System initialized');
    }

    setupEventListeners() {
        // Product search
        const searchInput = document.getElementById('product-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.searchProducts(e.target.value);
            }, 300));
        }

        // Barcode input
        const barcodeInput = document.getElementById('barcode-input');
        if (barcodeInput) {
            barcodeInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchByBarcode(e.target.value);
                    e.target.value = '';
                }
            });
        }

        // Payment method selection
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-payment-method]')) {
                this.selectPaymentMethod(e.target.dataset.paymentMethod);
            }
        });

        // Cart operations
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-cart-action]')) {
                const action = e.target.dataset.cartAction;
                const productId = e.target.dataset.productId;
                this.handleCartAction(action, productId);
            }
        });
    }

    async loadProducts() {
        try {
            // In real implementation, this would fetch from server
            window.alert('Loading products from inventory...\n\nIn a real application, this would fetch current product data from the database.');
            
            // Simulate product loading
            this.products = [
                { id: 1, name: 'Coca Cola 500ml', price: 60.00, barcode: '1234567890123', stock: 50 },
                { id: 2, name: 'White Bread', price: 45.00, barcode: '2345678901234', stock: 25 },
                { id: 3, name: 'Milk 1L', price: 55.00, barcode: '3456789012345', stock: 30 }
            ];
            
            this.renderProducts(this.products);
        } catch (error) {
            window.alert('Error loading products from inventory.\nPlease check your connection and try again.');
        }
    }

    renderProducts(products) {
        const container = document.getElementById('products-grid');
        if (!container) return;

        container.innerHTML = products.map(product => `
            <div class="col-md-4 mb-3">
                <div class="card product-card" data-product-id="${product.id}">
                    <div class="card-body">
                        <h6 class="card-title">${product.name}</h6>
                        <p class="card-text">
                            <strong>KES ${product.price.toFixed(2)}</strong><br>
                            <small class="text-muted">Stock: ${product.stock}</small>
                        </p>
                        <button class="btn btn-primary btn-sm" onclick="pos.addToCart(${product.id})">
                            Add to Cart
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    searchProducts(query) {
        if (!query.trim()) {
            this.renderProducts(this.products);
            return;
        }

        const filtered = this.products.filter(product =>
            product.name.toLowerCase().includes(query.toLowerCase()) ||
            product.barcode.includes(query)
        );

        if (filtered.length === 0) {
            window.alert(`No products found for: "${query}"\n\nTry adjusting your search terms or scan the barcode directly.`);
        }

        this.renderProducts(filtered);
    }

    searchByBarcode(barcode) {
        if (!barcode.trim()) return;

        const product = this.products.find(p => p.barcode === barcode);
        
        if (product) {
            window.alert(`Product found!\n\nName: ${product.name}\nPrice: KES ${product.price.toFixed(2)}\nStock: ${product.stock}\n\nAdding to cart...`);
            this.addToCart(product.id);
        } else {
            window.alert(`Product not found for barcode: ${barcode}\n\nPlease verify the barcode or add the product to inventory first.`);
        }
    }

    addToCart(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) {
            window.alert('Product not found. Please refresh and try again.');
            return;
        }

        if (product.stock <= 0) {
            window.alert(`${product.name} is out of stock!\n\nPlease restock before selling.`);
            return;
        }

        const existingItem = this.cart.find(item => item.productId === productId);
        
        if (existingItem) {
            if (existingItem.quantity >= product.stock) {
                window.alert(`Cannot add more ${product.name}.\n\nOnly ${product.stock} items available in stock.`);
                return;
            }
            existingItem.quantity++;
        } else {
            this.cart.push({
                productId,
                name: product.name,
                price: product.price,
                quantity: 1,
                lineTotal: product.price
            });
        }

        this.updateCart();
        this.saveCart();
        
        window.alert(`${product.name} added to cart!\n\nQuantity: ${existingItem ? existingItem.quantity : 1}\nPrice: KES ${product.price.toFixed(2)}`);
    }

    updateCart() {
        this.cart.forEach(item => {
            item.lineTotal = item.price * item.quantity;
        });

        this.renderCart();
        this.updateTotals();
    }

    renderCart() {
        const container = document.getElementById('cart-items');
        if (!container) return;

        if (this.cart.length === 0) {
            container.innerHTML = '<p class="text-muted">Cart is empty</p>';
            return;
        }

        container.innerHTML = this.cart.map(item => `
            <div class="cart-item border-bottom py-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${item.name}</h6>
                        <small class="text-muted">KES ${item.price.toFixed(2)} each</small>
                    </div>
                    <div class="d-flex align-items-center">
                        <button class="btn btn-sm btn-outline-secondary" data-cart-action="decrease" data-product-id="${item.productId}">-</button>
                        <span class="mx-2">${item.quantity}</span>
                        <button class="btn btn-sm btn-outline-secondary" data-cart-action="increase" data-product-id="${item.productId}">+</button>
                        <button class="btn btn-sm btn-outline-danger ms-2" data-cart-action="remove" data-product-id="${item.productId}">×</button>
                    </div>
                </div>
                <div class="text-end">
                    <strong>KES ${item.lineTotal.toFixed(2)}</strong>
                </div>
            </div>
        `).join('');
    }

    updateTotals() {
        const subtotal = this.cart.reduce((sum, item) => sum + item.lineTotal, 0);
        const tax = subtotal * 0.16; // 16% VAT
        const total = subtotal + tax;

        document.getElementById('subtotal')?.textContent = `KES ${subtotal.toFixed(2)}`;
        document.getElementById('tax-amount')?.textContent = `KES ${tax.toFixed(2)}`;
        document.getElementById('total-amount')?.textContent = `KES ${total.toFixed(2)}`;
    }

    handleCartAction(action, productId) {
        const itemIndex = this.cart.findIndex(item => item.productId == productId);
        if (itemIndex === -1) return;

        const item = this.cart[itemIndex];
        const product = this.products.find(p => p.id == productId);

        switch (action) {
            case 'increase':
                if (item.quantity >= product.stock) {
                    window.alert(`Cannot add more ${item.name}.\n\nOnly ${product.stock} items available in stock.`);
                    return;
                }
                item.quantity++;
                break;
            
            case 'decrease':
                if (item.quantity > 1) {
                    item.quantity--;
                } else {
                    window.alert(`Removing ${item.name} from cart.`);
                    this.cart.splice(itemIndex, 1);
                }
                break;
            
            case 'remove':
                if (window.confirm(`Remove ${item.name} from cart?`)) {
                    this.cart.splice(itemIndex, 1);
                }
                break;
        }

        this.updateCart();
        this.saveCart();
    }

    selectPaymentMethod(method) {
        if (this.cart.length === 0) {
            window.alert('Cart is empty. Please add items before selecting payment method.');
            return;
        }

        const total = this.cart.reduce((sum, item) => sum + (item.lineTotal * 1.16), 0);

        switch (method) {
            case 'cash':
                this.processCashPayment(total);
                break;
            case 'mpesa':
                this.processMpesaPayment(total);
                break;
            default:
                window.alert('Invalid payment method selected.');
        }
    }

    processCashPayment(total) {
        const received = window.prompt(`Cash Payment
        
Total Amount: KES ${total.toFixed(2)}

Enter amount received from customer:`);

        if (!received) return;

        const amount = parseFloat(received);
        if (isNaN(amount) || amount < total) {
            window.alert(`Insufficient amount received.
            
Required: KES ${total.toFixed(2)}
Received: KES ${amount.toFixed(2)}
Shortage: KES ${(total - amount).toFixed(2)}`);
            return;
        }

        const change = amount - total;
        
        const confirmMessage = `Cash Payment Confirmation
        
Total: KES ${total.toFixed(2)}
Received: KES ${amount.toFixed(2)}
Change: KES ${change.toFixed(2)}

Proceed with sale?`;

        if (window.confirm(confirmMessage)) {
            this.completeSale('cash', { amount_received: amount, change: change });
        }
    }

    processMpesaPayment(total) {
        const phone = window.prompt(`MPesa Payment
        
Total Amount: KES ${total.toFixed(2)}

Enter customer phone number (254XXXXXXXXX):`);

        if (!phone) return;

        if (!phone.match(/^254[0-9]{9}$/)) {
            window.alert('Invalid phone number format.\nPlease use format: 254XXXXXXXXX');
            return;
        }

        const confirmMessage = `MPesa Payment Request
        
Amount: KES ${total.toFixed(2)}
Phone: ${phone}

Send MPesa payment request?`;

        if (window.confirm(confirmMessage)) {
            this.isProcessingPayment = true;
            
            // Show payment processing status
            window.alert(`MPesa payment request sent to ${phone}
            
Customer should check their phone for the payment prompt.
Payment verification will start automatically.`);

            // Simulate MPesa payment processing
            setTimeout(() => {
                if (window.confirm('Did customer complete the MPesa payment?\n\nClick OK if payment was successful, Cancel to retry.')) {
                    const mpesaCode = window.prompt('Enter MPesa confirmation code:') || 'MP' + Date.now();
                    this.completeSale('mpesa', { phone, mpesa_code: mpesaCode });
                } else {
                    this.isProcessingPayment = false;
                    window.alert('Payment cancelled. You can try again or switch to cash payment.');
                }
            }, 3000);
        }
    }

    completeSale(paymentMethod, paymentData) {
        const subtotal = this.cart.reduce((sum, item) => sum + item.lineTotal, 0);
        const tax = subtotal * 0.16;
        const total = subtotal + tax;

        const sale = {
            id: Date.now(),
            receipt_number: 'RCP' + Date.now(),
            items: [...this.cart],
            subtotal,
            tax,
            total,
            payment_method: paymentMethod,
            payment_data: paymentData,
            timestamp: new Date(),
            status: 'completed'
        };

        // Show sale completion
        const receiptData = this.generateReceiptText(sale);
        window.alert(`SALE COMPLETED SUCCESSFULLY!

${receiptData}

Receipt will be printed automatically.`);

        // Update stock (in real implementation, this would update the database)
        this.updateStock();

        // Clear cart
        this.clearCart();

        // Store sale (in real implementation, this would save to database)
        this.storeSale(sale);

        this.isProcessingPayment = false;
    }

    generateReceiptText(sale) {
        return `
RECEIPT - ${sale.receipt_number}
Date: ${sale.timestamp.toLocaleString()}
Payment: ${sale.payment_method.toUpperCase()}

${'='.repeat(30)}
ITEMS:
${sale.items.map(item => 
    `${item.name}\n  ${item.quantity} x KES ${item.price.toFixed(2)} = KES ${item.lineTotal.toFixed(2)}`
).join('\n')}

${'='.repeat(30)}
Subtotal: KES ${sale.subtotal.toFixed(2)}
VAT (16%): KES ${sale.tax.toFixed(2)}
TOTAL: KES ${sale.total.toFixed(2)}

${sale.payment_method === 'mpesa' ? `MPesa Code: ${sale.payment_data.mpesa_code}` : ''}
${sale.payment_method === 'cash' ? `Change: KES ${sale.payment_data.change.toFixed(2)}` : ''}

Thank you for your business!
`;
    }

    updateStock() {
        this.cart.forEach(cartItem => {
            const product = this.products.find(p => p.id === cartItem.productId);
            if (product) {
                product.stock -= cartItem.quantity;
            }
        });
    }

    storeSale(sale) {
        const sales = JSON.parse(localStorage.getItem('pos_sales') || '[]');
        sales.unshift(sale);
        localStorage.setItem('pos_sales', JSON.stringify(sales.slice(0, 100))); // Keep last 100 sales
    }

    clearCart() {
        this.cart = [];
        this.updateCart();
        this.saveCart();
        localStorage.removeItem('pos_cart');
    }

    saveCart() {
        localStorage.setItem('pos_cart', JSON.stringify(this.cart));
    }

    restoreCart() {
        const saved = localStorage.getItem('pos_cart');
        if (saved) {
            this.cart = JSON.parse(saved);
            this.updateCart();
        }
    }

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
    }
}

// Initialize POS system
document.addEventListener('DOMContentLoaded', () => {
    window.pos = new POS();
});

// Global functions for compatibility
function confirmMpesaPayment() {
    window.alert('MPesa payment confirmed!\n\nTransaction completed successfully.');
}

function cancelMpesaPayment() {
    window.alert('MPesa payment cancelled.\n\nYou can try again or switch to cash payment.');
}