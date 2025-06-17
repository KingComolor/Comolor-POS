# MPesa Integration Guide

## Overview

This guide covers the complete MPesa integration for the Comolor POS system, including setup, configuration, testing, and troubleshooting for Kenya's mobile money payment system.

## MPesa Integration Architecture

### Components
- **Daraja API**: Safaricom's official MPesa API
- **C2B (Customer to Business)**: Customers pay to shop till numbers
- **STK Push**: Automated payment prompts to customer phones
- **Callback System**: Real-time payment confirmations
- **Transaction Logging**: Complete audit trail

### Payment Flow
1. Customer initiates payment via MPesa
2. System receives callback from Safaricom
3. Payment matched to transaction
4. Real-time status updates
5. Receipt generation and printing

## Setup Requirements

### 1. Safaricom Developer Account
1. Visit [developer.safaricom.co.ke](https://developer.safaricom.co.ke)
2. Create developer account
3. Create new app for MPesa integration
4. Get sandbox credentials for testing

### 2. Required Credentials
```bash
# Sandbox Environment
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=174379  # Sandbox shortcode
MPESA_PASSKEY=your_passkey
MPESA_ENVIRONMENT=sandbox

# Production Environment
MPESA_CONSUMER_KEY=your_prod_consumer_key
MPESA_CONSUMER_SECRET=your_prod_consumer_secret
MPESA_SHORTCODE=your_till_number
MPESA_PASSKEY=your_prod_passkey
MPESA_ENVIRONMENT=production
```

### 3. Callback URLs
Set up public URLs for MPesa callbacks:
```
Confirmation URL: https://yourdomain.com/mpesa/c2b/confirmation
Validation URL: https://yourdomain.com/mpesa/c2b/validation
Timeout URL: https://yourdomain.com/mpesa/c2b/timeout
```

## Configuration

### 1. Environment Setup
```python
# config.py
import os

class MPesaConfig:
    CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY')
    CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')
    SHORTCODE = os.environ.get('MPESA_SHORTCODE')
    PASSKEY = os.environ.get('MPESA_PASSKEY')
    ENVIRONMENT = os.environ.get('MPESA_ENVIRONMENT', 'sandbox')
    
    @property
    def base_url(self):
        if self.ENVIRONMENT == 'production':
            return 'https://api.safaricom.co.ke'
        return 'https://sandbox.safaricom.co.ke'
```

### 2. API Integration
```python
# utils/mpesa.py
class MpesaAPI:
    def __init__(self):
        self.consumer_key = MPesaConfig.CONSUMER_KEY
        self.consumer_secret = MPesaConfig.CONSUMER_SECRET
        self.base_url = MPesaConfig().base_url
        
    def get_access_token(self):
        """Get OAuth access token"""
        api_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(api_url, auth=(self.consumer_key, self.consumer_secret))
        return response.json()['access_token']
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK Push payment"""
        access_token = self.get_access_token()
        api_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'BusinessShortCode': MPesaConfig.SHORTCODE,
            'Password': self.generate_password(),
            'Timestamp': datetime.now().strftime('%Y%m%d%H%M%S'),
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': amount,
            'PartyA': phone_number,
            'PartyB': MPesaConfig.SHORTCODE,
            'PhoneNumber': phone_number,
            'CallBackURL': f'{request.url_root}mpesa/stk/callback',
            'AccountReference': account_reference,
            'TransactionDesc': transaction_desc
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        return response.json()
```

## Implementation

### 1. Customer Payment Process
```python
# routes/cashier.py
@cashier_bp.route('/create-sale', methods=['POST'])
def create_sale():
    # Create sale record
    sale = Sale(
        receipt_number=generate_receipt_number(),
        shop_id=current_user.shop_id,
        cashier_id=current_user.id,
        total_amount=total_amount,
        payment_method='mpesa',
        status='pending'
    )
    db.session.add(sale)
    db.session.commit()
    
    # Initiate MPesa payment
    if payment_method == 'mpesa':
        mpesa_api = MpesaAPI()
        result = mpesa_api.stk_push(
            phone_number=customer_phone,
            amount=total_amount,
            account_reference=sale.receipt_number,
            transaction_desc=f"Payment for {sale.receipt_number}"
        )
        
        return jsonify({
            'success': True,
            'sale_id': sale.id,
            'mpesa_checkout_id': result.get('CheckoutRequestID')
        })
```

### 2. Callback Handling
```python
# routes/mpesa.py
@mpesa_bp.route('/c2b/confirmation', methods=['POST'])
def c2b_confirmation():
    """Handle MPesa payment confirmation"""
    data = request.get_json()
    
    # Log transaction
    transaction = MpesaTransaction(
        transaction_type='sale',
        transaction_id=data['TransID'],
        bill_ref_number=data['BillRefNumber'],
        amount=data['TransAmount'],
        msisdn=data['MSISDN'],
        first_name=data['FirstName'],
        last_name=data['LastName'],
        transaction_time=datetime.strptime(data['TransTime'], '%Y%m%d%H%M%S'),
        is_processed=False
    )
    db.session.add(transaction)
    
    # Find matching sale
    sale = Sale.query.filter_by(receipt_number=data['BillRefNumber']).first()
    if sale:
        sale.status = 'completed'
        sale.mpesa_receipt = data['TransID']
        transaction.sale_id = sale.id
        transaction.shop_id = sale.shop_id
        transaction.is_processed = True
        
        # Update stock
        for item in sale.items:
            product = item.product
            product.stock_quantity -= item.quantity
            
            # Log stock movement
            stock_movement = StockMovement(
                product_id=product.id,
                movement_type='out',
                quantity=item.quantity,
                reference=f'sale_{sale.id}',
                created_by=sale.cashier_id
            )
            db.session.add(stock_movement)
    
    db.session.commit()
    return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})
```

### 3. Real-time Status Updates
```javascript
// static/js/mpesa.js
class MpesaIntegration {
    async startPaymentPolling(saleId) {
        this.pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/cashier/check-mpesa-payment/${saleId}`);
                const data = await response.json();
                
                if (data.payment_received) {
                    this.handlePaymentReceived(data);
                    this.stopPolling();
                } else if (data.timeout) {
                    this.handlePollingTimeout();
                    this.stopPolling();
                }
            } catch (error) {
                console.error('Error checking payment status:', error);
            }
        }, 2000); // Check every 2 seconds
    }
    
    handlePaymentReceived(paymentData) {
        // Show success message
        this.showSuccess(`Payment received! MPesa Code: ${paymentData.mpesa_receipt}`);
        
        // Update UI
        document.getElementById('payment-status').textContent = 'Payment Confirmed';
        document.getElementById('mpesa-code').textContent = paymentData.mpesa_receipt;
        
        // Enable print receipt button
        document.getElementById('print-receipt-btn').disabled = false;
    }
}
```

## Testing

### 1. Sandbox Testing
```python
# Test MPesa integration in sandbox
def test_mpesa_payment():
    mpesa_api = MpesaAPI()
    
    # Test STK Push
    result = mpesa_api.stk_push(
        phone_number='254712345678',  # Sandbox test number
        amount=100,
        account_reference='TEST001',
        transaction_desc='Test payment'
    )
    
    print(f"STK Push Result: {result}")
    
    # Simulate C2B payment
    result = mpesa_api.simulate_c2b_payment(
        amount=100,
        msisdn='254712345678',
        bill_ref_number='TEST001'
    )
    
    print(f"C2B Simulation Result: {result}")
```

### 2. Test Scenarios
1. **Successful Payment**: Customer pays correct amount
2. **Insufficient Funds**: Customer has insufficient balance
3. **Timeout**: Customer doesn't respond to STK push
4. **Wrong Amount**: Customer pays different amount
5. **Network Issues**: Connection problems during payment

## Production Deployment

### 1. Go-Live Checklist
- [ ] Production credentials obtained from Safaricom
- [ ] Callback URLs configured and accessible
- [ ] SSL certificates installed
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Monitoring setup
- [ ] Backup systems ready

### 2. Security Considerations
```python
# Validate callback authenticity
def validate_mpesa_callback(request):
    # Verify source IP
    allowed_ips = ['196.201.214.200', '196.201.214.206']  # Safaricom IPs
    client_ip = request.remote_addr
    
    if client_ip not in allowed_ips:
        return False
    
    # Additional validation logic
    return True
```

### 3. Error Handling
```python
# Comprehensive error handling
try:
    result = mpesa_api.stk_push(phone, amount, ref, desc)
    
    if result.get('ResponseCode') == '0':
        # Success
        return {'success': True, 'checkout_id': result['CheckoutRequestID']}
    else:
        # Handle specific error codes
        error_code = result.get('ResponseCode')
        error_msg = result.get('ResponseDescription', 'Unknown error')
        
        return {'success': False, 'error': f'{error_code}: {error_msg}'}
        
except requests.exceptions.RequestException as e:
    # Network error
    return {'success': False, 'error': 'Network error occurred'}
except Exception as e:
    # General error
    return {'success': False, 'error': 'Payment system error'}
```

## Troubleshooting

### Common Issues

1. **"Invalid Access Token"**
   - Check consumer key and secret
   - Verify environment (sandbox vs production)
   - Ensure credentials are active

2. **"Invalid Shortcode"**
   - Verify shortcode is correct
   - Check if shortcode is active
   - Ensure shortcode matches environment

3. **Callback Not Received**
   - Check callback URL accessibility
   - Verify HTTPS setup
   - Check firewall settings
   - Validate callback URL format

4. **Payment Shows as Pending**
   - Check MPesa transaction logs
   - Verify callback processing
   - Check database transaction records
   - Review system logs

### Monitoring and Logging
```python
# Enhanced logging
import logging

# Configure MPesa logger
mpesa_logger = logging.getLogger('mpesa')
mpesa_logger.setLevel(logging.INFO)

# Log all MPesa transactions
def log_mpesa_transaction(action, data, result):
    mpesa_logger.info(f"MPesa {action}: {data} -> {result}")

# Usage
log_mpesa_transaction('STK_PUSH', {'phone': phone, 'amount': amount}, result)
```

### Performance Optimization
1. **Connection Pooling**: Use connection pools for API calls
2. **Caching**: Cache access tokens (valid for 1 hour)
3. **Async Processing**: Handle callbacks asynchronously
4. **Rate Limiting**: Implement rate limiting for API calls

This comprehensive guide ensures reliable MPesa integration for seamless mobile money payments in your POS system.