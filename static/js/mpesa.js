// MPesa Integration JavaScript

class MpesaIntegration {
    constructor() {
        this.pollingInterval = null;
        this.maxPollingAttempts = 60; // 5 minutes
        this.pollingAttempts = 0;
        this.isPolling = false;
        
        this.init();
    }
    
    init() {
        // Initialize MPesa modal event listeners
        this.setupModalEvents();
    }
    
    setupModalEvents() {
        const modal = document.getElementById('mpesaPaymentModal');
        if (modal) {
            modal.addEventListener('hidden.bs.modal', () => {
                this.stopPolling();
                this.resetModal();
            });
        }
    }
    
    async startPaymentPolling(saleId) {
        if (this.isPolling) {
            window.alert('Payment check already in progress.\nPlease wait for current payment to complete.');
            return;
        }
        
        this.isPolling = true;
        this.pollingAttempts = 0;
        this.saleId = saleId;
        
        // Get payment details for user feedback
        const phoneNumber = document.getElementById('customer-phone')?.value || 'customer phone';
        const amount = document.getElementById('total-amount')?.textContent || 'total amount';
        
        window.alert(`MPesa payment request initiated!\n\nPhone: ${phoneNumber}\nAmount: ${amount}\n\nCustomer should check their phone for MPesa prompt.\nPayment will be verified automatically.`);
        
        console.log('Starting payment polling for sale:', saleId);
        
        this.pollingInterval = setInterval(() => {
            this.checkPaymentStatus();
        }, 3000); // Check every 3 seconds for better user experience
        
        // Also check immediately
        this.checkPaymentStatus();
    }
    
    async checkPaymentStatus() {
        this.pollingAttempts++;
        
        if (this.pollingAttempts > this.maxPollingAttempts) {
            this.handlePollingTimeout();
            return;
        }
        
        try {
            const response = await fetch(`/mpesa/payment/status/${this.saleId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.status === 'completed') {
                this.handlePaymentReceived(result);
            } else if (result.status === 'pending') {
                // Show till number for customer reference
                if (result.till_number) {
                    const tillInfo = document.getElementById('till-info');
                    if (tillInfo) {
                        tillInfo.innerHTML = `<strong>Till Number: ${result.till_number}</strong><br>Customer should send KES ${result.amount} to this till number`;
                    }
                }
                this.updatePollingStatus();
            } else {
                throw new Error(result.error || 'Payment check failed');
            }
        } catch (error) {
            console.error('Error checking payment status:', error);
            // Continue polling even if there's an error
        }
    }
    
    handlePaymentReceived(paymentData) {
        console.log('Payment received:', paymentData);
        
        this.stopPolling();
        
        // Show payment success prompt with details
        const paymentDetails = `PAYMENT RECEIVED SUCCESSFULLY!
        
Amount: KES ${paymentData.amount ? paymentData.amount.toFixed(2) : 'N/A'}
Phone: ${paymentData.customer_phone || 'N/A'}
Customer: ${paymentData.customer_name || 'Walk-in Customer'}
MPesa Code: ${paymentData.mpesa_receipt || 'N/A'}
Time: ${new Date().toLocaleString()}

Transaction completed successfully!`;

        window.alert(paymentDetails);
        
        // Hide the waiting status
        const paymentStatus = document.getElementById('paymentStatus');
        if (paymentStatus) {
            paymentStatus.style.display = 'none';
        }
        
        // Show payment confirmation details
        this.displayPaymentConfirmation(paymentData);
        
        // Play success sound
        this.playPaymentSuccessSound();
        
        // Store payment data for confirmation
        this.pendingPaymentData = paymentData;
    }
    
    displayPaymentConfirmation(paymentData) {
        const confirmationDiv = document.getElementById('paymentConfirmed');
        if (confirmationDiv) {
            confirmationDiv.style.display = 'block';
            
            // Update confirmation details
            const elements = {
                'confirmedAmount': paymentData.amount.toFixed(2),
                'confirmedPhone': paymentData.phone,
                'confirmedCustomer': paymentData.customer_name || 'Walk-in Customer',
                'confirmedCode': paymentData.transaction_id,
                'confirmedTime': this.formatDateTime(paymentData.transaction_time)
            };
            
            for (const [elementId, value] of Object.entries(elements)) {
                const element = document.getElementById(elementId);
                if (element) {
                    element.textContent = value;
                }
            }
            
            // Show the confirm button
            const confirmBtn = document.getElementById('confirmPaymentBtn');
            if (confirmBtn) {
                confirmBtn.style.display = 'block';
            }
        }
    }
    
    async confirmPayment() {
        if (!this.pendingPaymentData) {
            console.error('No pending payment data');
            return;
        }
        
        try {
            const response = await fetch('/cashier/api/mpesa/confirm-payment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mpesa_id: this.pendingPaymentData.mpesa_id,
                    sale_id: this.saleId
                })
            });
            
            if (response.ok) {
                this.handlePaymentConfirmed();
            } else {
                const error = await response.json();
                this.showError(error.error || 'Failed to confirm payment');
            }
        } catch (error) {
            console.error('Error confirming payment:', error);
            this.showError('Network error occurred');
        }
    }
    
    handlePaymentConfirmed() {
        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('mpesaPaymentModal'));
        if (modal) {
            modal.hide();
        }
        
        // Show success message
        this.showSuccess('Payment confirmed successfully!');
        
        // Trigger successful payment event
        const event = new CustomEvent('paymentConfirmed', {
            detail: {
                saleId: this.saleId,
                paymentData: this.pendingPaymentData
            }
        });
        document.dispatchEvent(event);
        
        // Reset
        this.resetModal();
        this.pendingPaymentData = null;
        this.saleId = null;
    }
    
    handlePollingTimeout() {
        console.log('Payment polling timeout');
        this.stopPolling();
        
        // Show comprehensive timeout alert with options
        const timeoutMessage = `PAYMENT TIMEOUT - No payment received

Possible reasons:
• Customer cancelled the transaction
• Customer entered wrong PIN
• Network connectivity issues
• Insufficient funds in customer account

Recommended actions:
1. Ask customer to check their phone for any pending MPesa prompts
2. Verify the phone number is correct
3. Try the payment again
4. Switch to cash payment if needed

Would you like to try the payment again?`;

        const retry = window.confirm(timeoutMessage);
        
        if (retry) {
            // Reset and allow retry
            this.resetModal();
            window.alert('Ready to retry payment. Please ensure customer phone number is correct and customer has sufficient funds.');
        } else {
            // Switch to cash or cancel
            window.alert('Payment cancelled. You can switch to cash payment or start a new transaction.');
        }
        
        this.showError('Payment timeout. Please try again or contact customer support.');
        
        // Optional: Auto-close modal after timeout
        setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(document.getElementById('mpesaPaymentModal'));
            if (modal) {
                modal.hide();
            }
        }, 5000);
    }
    
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        this.isPolling = false;
        this.pollingAttempts = 0;
    }
    
    resetModal() {
        // Reset modal to initial state
        const paymentStatus = document.getElementById('paymentStatus');
        const paymentConfirmed = document.getElementById('paymentConfirmed');
        const confirmBtn = document.getElementById('confirmPaymentBtn');
        
        if (paymentStatus) paymentStatus.style.display = 'block';
        if (paymentConfirmed) paymentConfirmed.style.display = 'none';
        if (confirmBtn) confirmBtn.style.display = 'none';
        
        this.pendingPaymentData = null;
    }
    
    updatePollingStatus() {
        // Update the waiting message with attempt count
        const statusDiv = document.getElementById('paymentStatus');
        if (statusDiv) {
            const timeRemaining = Math.max(0, this.maxPollingAttempts - this.pollingAttempts);
            const minutesRemaining = Math.ceil(timeRemaining * 5 / 60);
            
            const messageElement = statusDiv.querySelector('p');
            if (messageElement) {
                messageElement.innerHTML = `
                    Waiting for payment confirmation...<br>
                    <small class="text-muted">Timeout in ${minutesRemaining} minute${minutesRemaining !== 1 ? 's' : ''}</small>
                `;
            }
        }
    }
    
    formatDateTime(dateTimeString) {
        try {
            const date = new Date(dateTimeString);
            return date.toLocaleString('en-KE', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateTimeString;
        }
    }
    
    playPaymentSuccessSound() {
        try {
            // Create a pleasant success sound
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create three-tone success melody
            const frequencies = [523.25, 659.25, 783.99]; // C5, E5, G5
            
            frequencies.forEach((freq, index) => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(freq, audioContext.currentTime);
                oscillator.type = 'sine';
                
                const startTime = audioContext.currentTime + (index * 0.2);
                gainNode.gain.setValueAtTime(0, startTime);
                gainNode.gain.linearRampToValueAtTime(0.2, startTime + 0.05);
                gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.3);
                
                oscillator.start(startTime);
                oscillator.stop(startTime + 0.3);
            });
        } catch (error) {
            console.log('Audio not available');
        }
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        // Create notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info';
        
        notification.innerHTML = `
            <i data-feather="${icon}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Initialize feather icons for the notification
        feather.replace();
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    // Simulate payment for testing (development only)
    simulatePayment(amount, phone = '254712345678') {
        if (process.env.NODE_ENV === 'development') {
            setTimeout(() => {
                const fakePaymentData = {
                    payment_received: true,
                    amount: amount,
                    phone: phone,
                    customer_name: 'Test Customer',
                    transaction_id: 'TEST' + Date.now(),
                    transaction_time: new Date().toISOString(),
                    mpesa_id: Math.floor(Math.random() * 1000)
                };
                
                this.handlePaymentReceived(fakePaymentData);
            }, 3000); // Simulate 3 second delay
        }
    }
}

// Global MPesa instance
window.mpesaIntegration = new MpesaIntegration();

// Global functions for modal actions
function confirmMpesaPayment() {
    if (window.mpesaIntegration) {
        window.mpesaIntegration.confirmPayment();
    }
}

function cancelMpesaPayment() {
    if (window.mpesaIntegration) {
        window.mpesaIntegration.stopPolling();
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('mpesaPaymentModal'));
        if (modal) {
            modal.hide();
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Listen for payment events from POS system
    document.addEventListener('mpesaPaymentStarted', function(event) {
        if (window.mpesaIntegration && event.detail.saleId) {
            window.mpesaIntegration.startPaymentPolling(event.detail.saleId);
        }
    });
});

// Export for modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MpesaIntegration };
}
