# MPesa Integration Data Flow - Comolor POS

This document explains how MPesa C2B (Customer to Business) transactions are handled in the Comolor POS system.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Data Flow](#data-flow)
- [Transaction States](#transaction-states)
- [Database Schema](#database-schema)
- [Security Considerations](#security-considerations)
- [Error Handling](#error-handling)
- [Testing](#testing)

## Overview

The Comolor POS system integrates with Safaricom's Daraja API to process MPesa payments through the C2B (Customer to Business) payment model. This allows customers to pay for goods by sending money to the shop's till number.

### Key Components
- **Daraja API**: Safaricom's payment gateway
- **C2B Registration**: Webhook URL registration with Safaricom
- **Payment Polling**: Real-time status checking
- **Transaction Logging**: Complete audit trail
- **Callback Processing**: Asynchronous payment confirmation

## Architecture

```
Customer Mobile → MPesa → Safaricom → Daraja API → Comolor POS
                                         ↓
                                    Webhook Callbacks
                                         ↓
                                   Database Updates
                                         ↓
                                   Real-time Polling
                                         ↓
                                   UI Status Updates
```

### Integration Points
1. **POS Terminal**: Initiates payment request
2. **MPesa API**: Handles payment processing
3. **Webhook Endpoints**: Receives payment confirmations
4. **Database**: Stores transaction records
5. **Frontend Polling**: Updates UI in real-time

## Data Flow

### 1. Sale Initiation
```javascript
// Frontend initiates sale
const saleData = {
    items: cartItems,
    payment_method: 'mpesa',
    amount: totalAmount
};

// POST to /cashier/sale/create
```

### 2. Sale Creation
```python
# Backend creates pending sale
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
```

### 3. Payment Display
```javascript
// Frontend shows MPesa payment modal
showMpesaModal({
    amount: sale.total_amount,
    till_number: shop.till_number,
    reference: sale.receipt_number
});

// Start polling for payment
startPaymentPolling(sale.id);
```

### 4. Customer Payment
```
Customer Action:
1. Opens MPesa on mobile phone
2. Selects "Pay Bill" option
3. Enters business number (till number)
4. Enters amount
5. Enters reference (receipt number)
6. Enters MPesa PIN
7. Confirms payment
```

### 5. MPesa Processing
```
MPesa Internal Flow:
1. Validates customer account and PIN
2. Debits customer account
3. Credits business account
4. Generates transaction ID
5. Sends callback to registered URLs
```

### 6. Callback Reception
```python
@mpesa.route('/confirmation', methods=['POST'])
def c2b_confirmation():
    """Handle MPesa C2B confirmation callback"""
    try:
        data = request.get_json()
        
        # Extract transaction details
        transaction_data = {
            'transaction_id': data['TransID'],
            'amount': Decimal(data['TransAmount']),
            'msisdn': data['MSISDN'],
            'bill_ref_number': data['BillRefNumber'],
            'transaction_time': parse_mpesa_time(data['TransTime']),
            'first_name': data.get('FirstName', ''),
            'last_name': data.get('LastName', '')
        }
        
        # Process transaction
        process_mpesa_transaction(transaction_data)
        
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})
        
    except Exception as e:
        log_error('MPesa callback error', e)
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Failed'})
```

### 7. Transaction Processing
```python
def process_mpesa_transaction(transaction_data):
    """Process incoming MPesa transaction"""
    
    # Find matching sale by reference number
    sale = Sale.query.filter_by(
        receipt_number=transaction_data['bill_ref_number']
    ).first()
    
    if not sale:
        # Log unmatched transaction
        create_unmatched_transaction_log(transaction_data)
        return
    
    # Verify amount matches
    if sale.total_amount != transaction_data['amount']:
        log_amount_mismatch(sale, transaction_data)
        return
    
    # Create transaction record
    mpesa_transaction = MpesaTransaction(
        transaction_type='sale',
        transaction_id=transaction_data['transaction_id'],
        bill_ref_number=transaction_data['bill_ref_number'],
        amount=transaction_data['amount'],
        msisdn=transaction_data['msisdn'],
        first_name=transaction_data['first_name'],
        last_name=transaction_data['last_name'],
        transaction_time=transaction_data['transaction_time'],
        shop_id=sale.shop_id,
        sale_id=sale.id,
        is_processed=True
    )
    
    # Update sale status
    sale.status = 'completed'
    sale.mpesa_receipt = transaction_data['transaction_id']
    
    # Update inventory
    for item in sale.items:
        product = item.product
        product.stock_quantity -= item.quantity
        
        # Create stock movement record
        movement = StockMovement(
            product_id=product.id,
            movement_type='out',
            quantity=item.quantity,
            reference=f"sale_{sale.id}",
            created_by=sale.cashier_id
        )
        db.session.add(movement)
    
    db.session.add(mpesa_transaction)
    db.session.commit()
    
    # Log successful transaction
    log_audit(
        user_id=sale.cashier_id,
        action='mpesa_payment_received',
        entity_type='sale',
        entity_id=sale.id
    )
```

### 8. Frontend Polling
```javascript
async function checkPaymentStatus(saleId) {
    try {
        const response = await fetch(`/cashier/mpesa/check/${saleId}`);
        const data = await response.json();
        
        if (data.payment_received) {
            // Payment confirmed
            handlePaymentSuccess(data.payment_data);
            stopPolling();
        }
        
    } catch (error) {
        console.error('Payment check error:', error);
    }
}

// Poll every 5 seconds for up to 5 minutes
const pollInterval = setInterval(checkPaymentStatus, 5000);
setTimeout(() => {
    clearInterval(pollInterval);
    handlePaymentTimeout();
}, 300000); // 5 minutes
```

### 9. Payment Confirmation
```python
@cashier.route('/mpesa/check/<int:sale_id>')
@require_role('cashier')
def check_mpesa_payment(sale_id):
    """Check if MPesa payment has been received for a sale"""
    
    sale = Sale.query.get_or_404(sale_id)
    
    # Check if payment received
    mpesa_transaction = MpesaTransaction.query.filter_by(
        sale_id=sale_id,
        is_processed=True
    ).first()
    
    if mpesa_transaction:
        return jsonify({
            'payment_received': True,
            'payment_data': {
                'transaction_id': mpesa_transaction.transaction_id,
                'amount': str(mpesa_transaction.amount),
                'phone': mpesa_transaction.msisdn,
                'customer_name': f"{mpesa_transaction.first_name} {mpesa_transaction.last_name}".strip(),
                'transaction_time': mpesa_transaction.transaction_time.isoformat()
            }
        })
    
    return jsonify({'payment_received': False})
```

## Transaction States

### Sale Status Flow
```
1. pending    → Initial state when sale created
2. completed  → Payment received and confirmed
3. failed     → Payment failed or timed out
4. refunded   → Sale refunded (separate process)
```

### MPesa Transaction States
```
1. received   → Callback received from MPesa
2. processed  → Transaction matched to sale
3. unmatched  → No matching sale found
4. failed     → Processing error occurred
```

## Database Schema

### Sales Table
```sql
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    receipt_number VARCHAR(50) UNIQUE NOT NULL,
    shop_id INTEGER REFERENCES shops(id),
    cashier_id INTEGER REFERENCES users(id),
    total_amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    mpesa_receipt VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### MPesa Transactions Table
```sql
CREATE TABLE mpesa_transactions (
    id SERIAL PRIMARY KEY,
    transaction_type VARCHAR(20) NOT NULL,
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    bill_ref_number VARCHAR(100),
    amount DECIMAL(10,2) NOT NULL,
    msisdn VARCHAR(15) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    transaction_time TIMESTAMP NOT NULL,
    shop_id INTEGER REFERENCES shops(id),
    sale_id INTEGER REFERENCES sales(id),
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes for Performance
```sql
CREATE INDEX idx_sales_receipt_number ON sales(receipt_number);
CREATE INDEX idx_sales_status ON sales(status);
CREATE INDEX idx_mpesa_transaction_id ON mpesa_transactions(transaction_id);
CREATE INDEX idx_mpesa_bill_ref ON mpesa_transactions(bill_ref_number);
CREATE INDEX idx_mpesa_sale_id ON mpesa_transactions(sale_id);
```

## Security Considerations

### Callback Authentication
```python
def verify_mpesa_callback(request):
    """Verify MPesa callback authenticity"""
    
    # Check source IP (Safaricom IPs only)
    allowed_ips = ['196.201.214.200', '196.201.214.206']
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    if client_ip not in allowed_ips:
        return False
    
    # Verify callback structure
    required_fields = ['TransID', 'TransAmount', 'MSISDN', 'BillRefNumber']
    data = request.get_json()
    
    return all(field in data for field in required_fields)
```

### Data Validation
```python
def validate_transaction_data(data):
    """Validate incoming transaction data"""
    
    # Amount validation
    try:
        amount = Decimal(data['TransAmount'])
        if amount <= 0:
            raise ValueError("Invalid amount")
    except (ValueError, InvalidOperation):
        return False, "Invalid amount format"
    
    # Phone number validation
    msisdn = data['MSISDN']
    if not re.match(r'^254\d{9}$', msisdn):
        return False, "Invalid phone number format"
    
    # Reference validation
    bill_ref = data['BillRefNumber']
    if not re.match(r'^RCP-\d{8}-\d+$', bill_ref):
        return False, "Invalid reference format"
    
    return True, "Valid"
```

### Idempotency
```python
def ensure_transaction_idempotency(transaction_id):
    """Ensure transaction is processed only once"""
    
    existing = MpesaTransaction.query.filter_by(
        transaction_id=transaction_id
    ).first()
    
    if existing:
        logger.info(f"Duplicate transaction ignored: {transaction_id}")
        return False
    
    return True
```

## Error Handling

### Common Error Scenarios

1. **Callback Timeout**
   - Customer doesn't complete payment
   - Network issues between MPesa and system
   - System downtime during payment

2. **Amount Mismatch**
   - Customer pays wrong amount
   - Currency conversion issues
   - Rounding differences

3. **Reference Mismatch**
   - Customer enters wrong reference
   - Typos in receipt number
   - Old receipt number reused

4. **Duplicate Transactions**
   - MPesa resends callback
   - Network retry mechanisms
   - System processing delays

### Error Recovery
```python
def handle_payment_errors():
    """Handle various payment error scenarios"""
    
    # Check for unmatched transactions
    unmatched = MpesaTransaction.query.filter_by(
        sale_id=None,
        is_processed=False
    ).all()
    
    for transaction in unmatched:
        # Try to match by amount and timeframe
        potential_sales = Sale.query.filter(
            Sale.total_amount == transaction.amount,
            Sale.created_at >= transaction.transaction_time - timedelta(hours=1),
            Sale.status == 'pending'
        ).all()
        
        if len(potential_sales) == 1:
            # Single match found - auto-reconcile
            sale = potential_sales[0]
            transaction.sale_id = sale.id
            transaction.is_processed = True
            sale.status = 'completed'
            sale.mpesa_receipt = transaction.transaction_id
            
            db.session.commit()
            
            # Notify relevant parties
            notify_payment_reconciled(sale, transaction)
```

## Testing

### Sandbox Testing
```python
# Sandbox environment configuration
MPESA_ENVIRONMENT = 'sandbox'
MPESA_BASE_URL = 'https://sandbox.safaricom.co.ke'

# Test credentials (sandbox)
MPESA_CONSUMER_KEY = 'sandbox_consumer_key'
MPESA_CONSUMER_SECRET = 'sandbox_consumer_secret'
MPESA_SHORTCODE = '174379'  # Sandbox shortcode
```

### Test Scenarios
1. **Successful Payment Flow**
   - Create sale
   - Customer pays correct amount
   - Callback received and processed
   - Sale completed successfully

2. **Timeout Scenario**
   - Create sale
   - No payment received within timeout
   - Sale marked as failed
   - Inventory not updated

3. **Amount Mismatch**
   - Create sale for KES 100
   - Customer pays KES 150
   - Transaction logged but sale remains pending
   - Manual reconciliation required

4. **Duplicate Callback**
   - Payment processed successfully
   - Duplicate callback received
   - Second callback ignored
   - No duplicate processing

### Testing Tools
```python
# Simulate MPesa callback for testing
def simulate_mpesa_payment(sale_id, amount, phone='254700000000'):
    """Simulate MPesa payment for testing"""
    
    sale = Sale.query.get(sale_id)
    
    callback_data = {
        'TransactionType': 'Pay Bill',
        'TransID': f'TEST{random.randint(100000, 999999)}',
        'TransTime': datetime.now().strftime('%Y%m%d%H%M%S'),
        'TransAmount': str(amount),
        'BusinessShortCode': '123456',
        'BillRefNumber': sale.receipt_number,
        'MSISDN': phone,
        'FirstName': 'TEST',
        'LastName': 'CUSTOMER'
    }
    
    # Send to confirmation endpoint
    response = requests.post(
        'http://localhost:5000/mpesa/confirmation',
        json=callback_data
    )
    
    return response.status_code == 200
```

## Monitoring and Analytics

### Key Metrics
- Payment success rate
- Average payment processing time
- Failed transaction analysis
- Callback response times
- Revenue reconciliation

### Logging
```python
# Transaction logging
logger.info(f"MPesa payment received: {transaction_id} - {amount}")
logger.warning(f"Amount mismatch: Expected {expected}, Received {actual}")
logger.error(f"Callback processing failed: {error_message}")
```

### Alerts
- Failed callback processing
- High number of unmatched transactions
- Unusual payment patterns
- System connectivity issues

This comprehensive data flow ensures reliable, secure, and auditable MPesa payment processing within the Comolor POS system.