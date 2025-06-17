# MPesa Integration Guide for Real-World Applications

## What is MPesa Integration?

MPesa is Kenya's mobile money system used by millions. Integrating it into your POS system allows customers to pay directly from their phones to your shop's till number, making transactions fast and cashless.

**Real-World Scenario:**
1. Customer buys items worth KES 500
2. Cashier gives them the till number: 123456
3. Customer sends money via MPesa: *150*01*123456*500#
4. Your system automatically receives payment confirmation
5. Receipt is printed instantly

## How MPesa Works for Businesses

### MPesa Paybill vs Till Number

**Paybill (For Large Businesses):**
- Format: *150*01*PaybillNumber*AccountNumber*Amount#
- Example: *150*01*400200*JohnAccount*500#
- Requires business registration
- Can have account numbers for different customers

**Till Number (For Small Shops - What You'll Use):**
- Format: *150*01*TillNumber*Amount#
- Example: *150*01*123456*500#
- Easier to get from Safaricom
- Perfect for retail shops

## Getting Started with MPesa (Step by Step)

### Step 1: Apply for MPesa Till Number

**Visit Safaricom Shop:**
1. Bring your business registration certificate
2. Bring your ID/Passport
3. Fill MPesa application form
4. Get your till number (e.g., 123456)

**What You Get:**
- Unique till number for your shop
- MPesa statement via SMS
- Access to MPesa portal for reports

### Step 2: Apply for Daraja API Access

**Daraja API** is Safaricom's system that lets your application automatically receive payment notifications.

**Application Process:**
1. Go to https://developer.safaricom.co.ke
2. Create developer account
3. Apply for production access
4. Provide:
   - Business details
   - Application description
   - Technical integration plan
   - Your website/app URL

**What You Get:**
- Consumer Key
- Consumer Secret
- Passkey
- Access to sandbox for testing

### Step 3: Technical Requirements

**Your Server Must Have:**
- SSL certificate (HTTPS required)
- Public IP address (accessible from internet)
- Callback endpoints for MPesa notifications

## Understanding MPesa API Components

### 1. Consumer Key & Consumer Secret
```
Consumer Key: xxxxxxxxxxxxxxxxxxx
Consumer Secret: yyyyyyyyyyyyyyyyyyy
```
These are like username/password for your application to access MPesa API.

### 2. Passkey
```
Passkey: bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
```
This is used to generate security passwords for API calls.

### 3. Shortcode (Till Number)
```
Shortcode: 174379  (Your till number)
```
This is where customers send money.

### 4. Callback URLs
```
Confirmation URL: https://yourdomain.com/mpesa/c2b/confirmation
Validation URL: https://yourdomain.com/mpesa/c2b/validation
```
MPesa sends payment notifications to these URLs.

## How Your Current System Works

### 1. Customer Payment Process

```python
# When customer wants to pay with MPesa
@app.route('/create-sale', methods=['POST'])
def create_sale():
    # Create sale record
    sale = Sale(
        shop_id=current_user.shop_id,
        total_amount=500.00,
        payment_method='mpesa',
        status='pending'  # Waiting for MPesa confirmation
    )
    db.session.add(sale)
    db.session.commit()
    
    # Show customer the till number
    till_number = current_user.shop.till_number
    return {
        'sale_id': sale.id,
        'till_number': till_number,
        'amount': 500.00,
        'instructions': f'Send KES 500 to till number {till_number}'
    }
```

### 2. MPesa Sends Confirmation

When customer pays, MPesa automatically calls your confirmation URL:

```python
@app.route('/mpesa/c2b/confirmation', methods=['POST'])
def c2b_confirmation():
    # MPesa sends payment details
    data = request.get_json()
    
    """
    MPesa sends data like:
    {
        "TransactionType": "Pay Bill",
        "TransID": "LGR019G3J2",
        "TransTime": "20191122063845",
        "TransAmount": "500.00",
        "BusinessShortCode": "123456",
        "BillRefNumber": "account123",
        "InvoiceNumber": "",
        "MSISDN": "254708374149",
        "FirstName": "John",
        "MiddleName": "Doe",
        "LastName": "Customer"
    }
    """
    
    # Find the sale and mark as paid
    amount = float(data['TransAmount'])
    till_number = data['BusinessShortCode']
    
    # Find pending sale with matching amount and shop
    shop = Shop.query.filter_by(till_number=till_number).first()
    sale = Sale.query.filter_by(
        shop_id=shop.id,
        total_amount=amount,
        status='pending'
    ).first()
    
    if sale:
        # Payment confirmed!
        sale.status = 'completed'
        sale.mpesa_receipt = data['TransID']
        sale.customer_phone = data['MSISDN']
        sale.customer_name = f"{data['FirstName']} {data['LastName']}"
        db.session.commit()
        
        # Update inventory
        for item in sale.items:
            product = item.product
            product.stock_quantity -= item.quantity
        db.session.commit()
    
    return {'ResultCode': 0, 'ResultDesc': 'Success'}
```

### 3. Real-Time Updates

Your POS interface polls for payment status:

```javascript
// Frontend JavaScript checks payment status
function checkPaymentStatus(saleId) {
    fetch(`/check-payment-status/${saleId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'completed') {
                // Payment received!
                showSuccessMessage('Payment received!');
                printReceipt(saleId);
            } else {
                // Still waiting, check again in 3 seconds
                setTimeout(() => checkPaymentStatus(saleId), 3000);
            }
        });
}
```

## Real-World Setup Process

### Phase 1: Sandbox Testing (Development)

**1. Get Sandbox Credentials:**
```
Environment: sandbox
Consumer Key: sandbox_consumer_key
Consumer Secret: sandbox_consumer_secret
Shortcode: 174379 (Safaricom test till)
Passkey: sandbox_passkey
```

**2. Test with Sandbox:**
- Use test phone numbers: 254708374149
- Use small amounts: KES 1-100
- Test all payment scenarios

**3. Set Environment Variables:**
```bash
MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY=sandbox_key
MPESA_CONSUMER_SECRET=sandbox_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=sandbox_passkey
```

### Phase 2: Production Setup

**1. Get Production Credentials:**
After Safaricom approves your application:
```
Environment: production
Consumer Key: live_consumer_key
Consumer Secret: live_consumer_secret  
Shortcode: 123456 (Your actual till number)
Passkey: live_passkey
```

**2. Configure Callback URLs:**
Tell Safaricom where to send notifications:
```
Confirmation URL: https://yourapp.onrender.com/mpesa/c2b/confirmation
Validation URL: https://yourapp.onrender.com/mpesa/c2b/validation
```

**3. Register URLs with MPesa:**
```python
def register_c2b_urls():
    """Register callback URLs with MPesa"""
    access_token = get_mpesa_access_token()
    
    payload = {
        "ShortCode": config.MPESA_SHORTCODE,
        "ResponseType": "Complete",
        "ConfirmationURL": "https://yourapp.onrender.com/mpesa/c2b/confirmation",
        "ValidationURL": "https://yourapp.onrender.com/mpesa/c2b/validation"
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'https://api.safaricom.co.ke/mpesa/c2b/v1/registerurl',
        json=payload,
        headers=headers
    )
    
    return response.json()
```

## Multi-Tenant MPesa Setup

### Each Shop Gets Own Till Number

```python
class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    till_number = db.Column(db.String(20), unique=True)  # Each shop has unique till
    
    # MPesa integration per shop
    mpesa_shortcode = db.Column(db.String(20))  # Same as till_number usually
    mpesa_active = db.Column(db.Boolean, default=False)
```

### Payment Processing Per Shop

```python
@app.route('/mpesa/c2b/confirmation', methods=['POST'])
def c2b_confirmation():
    data = request.get_json()
    
    # Find which shop received payment
    till_number = data['BusinessShortCode']
    shop = Shop.query.filter_by(till_number=till_number).first()
    
    if not shop:
        # Unknown till number
        return {'ResultCode': 1, 'ResultDesc': 'Unknown till number'}
    
    # Process payment for this specific shop
    process_shop_payment(shop, data)
    
    return {'ResultCode': 0, 'ResultDesc': 'Success'}
```

## License Payment System

Your system has a special feature for shop license payments:

### Super Admin Till for License Payments

```python
# License payments go to super admin's till
SUPER_ADMIN_TILL = "0797237383"  # Your personal MPesa number

@app.route('/pay-license', methods=['POST'])
def pay_license():
    shop_id = request.form['shop_id']
    amount = 1000.00  # KES 1000 for 1 month license
    
    # Create license payment record
    payment = LicensePayment(
        shop_id=shop_id,
        amount=amount,
        status='pending'
    )
    db.session.add(payment)
    db.session.commit()
    
    return render_template('pay_license.html', {
        'till_number': SUPER_ADMIN_TILL,
        'amount': amount,
        'reference': f'LICENSE-{shop_id}'
    })
```

### License Activation Process

```python
@app.route('/mpesa/license/confirmation', methods=['POST'])  
def license_confirmation():
    data = request.get_json()
    
    if data['MSISDN'] == SUPER_ADMIN_TILL:
        # This is a license payment
        reference = data.get('BillRefNumber', '')
        
        if 'LICENSE-' in reference:
            shop_id = reference.split('-')[1]
            shop = Shop.query.get(shop_id)
            
            # Activate shop license
            shop.license_expires = datetime.utcnow() + timedelta(days=30)
            shop.is_active = True
            db.session.commit()
            
            # Send confirmation SMS to shop owner
            send_sms(shop.phone, f'License activated for {shop.name}. Valid until {shop.license_expires.strftime("%Y-%m-%d")}')
    
    return {'ResultCode': 0, 'ResultDesc': 'Success'}
```

## Security Best Practices

### 1. Validate MPesa Requests

```python
def validate_mpesa_request(request_data):
    """Verify request is actually from Safaricom"""
    
    # Check required fields
    required_fields = ['TransactionType', 'TransID', 'TransAmount', 'BusinessShortCode']
    for field in required_fields:
        if field not in request_data:
            return False
    
    # Verify shortcode belongs to you
    shortcode = request_data['BusinessShortCode']
    if not Shop.query.filter_by(till_number=shortcode).first():
        return False
    
    # Verify amount is reasonable
    amount = float(request_data['TransAmount'])
    if amount <= 0 or amount > 100000:  # Max KES 100,000
        return False
    
    return True
```

### 2. Handle Duplicate Payments

```python
def process_mpesa_payment(data):
    """Process payment and handle duplicates"""
    
    transaction_id = data['TransID']
    
    # Check if already processed
    existing = MpesaTransaction.query.filter_by(
        transaction_id=transaction_id
    ).first()
    
    if existing:
        # Already processed, ignore
        return {'ResultCode': 0, 'ResultDesc': 'Already processed'}
    
    # Process new payment
    transaction = MpesaTransaction(
        transaction_id=transaction_id,
        amount=float(data['TransAmount']),
        msisdn=data['MSISDN'],
        business_short_code=data['BusinessShortCode'],
        transaction_time=parse_mpesa_time(data['TransTime']),
        is_processed=False
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    # Process the payment
    process_transaction(transaction)
```

### 3. Error Handling

```python
@app.route('/mpesa/c2b/confirmation', methods=['POST'])
def c2b_confirmation():
    try:
        data = request.get_json()
        
        if not validate_mpesa_request(data):
            return {'ResultCode': 1, 'ResultDesc': 'Invalid request'}
        
        result = process_mpesa_payment(data)
        return result
        
    except Exception as e:
        # Log error
        app.logger.error(f'MPesa confirmation error: {str(e)}')
        
        # Still return success to MPesa to avoid retries
        return {'ResultCode': 0, 'ResultDesc': 'Processed with errors'}
```

## Testing Your Integration

### 1. Sandbox Testing

```python
# Test payment simulation
def simulate_mpesa_payment(till_number, amount, phone_number):
    """Simulate MPesa payment for testing"""
    
    # This would be called by Safaricom sandbox
    test_data = {
        "TransactionType": "Pay Bill",
        "TransID": f"TEST{random.randint(1000,9999)}",
        "TransTime": datetime.now().strftime("%Y%m%d%H%M%S"),
        "TransAmount": str(amount),
        "BusinessShortCode": till_number,
        "MSISDN": phone_number,
        "BillRefNumber": "",
        "InvoiceNumber": "",
        "FirstName": "Test",
        "MiddleName": "",
        "LastName": "Customer"
    }
    
    # Send to your confirmation endpoint
    response = requests.post(
        'http://localhost:5000/mpesa/c2b/confirmation',
        json=test_data
    )
    
    return response.json()
```

### 2. Production Testing

```bash
# Test with real small amounts
# Send KES 1 to your till number
# Check if your system receives notification
# Verify database updates correctly
```

## Common Issues and Solutions

### 1. Callback URL Not Accessible

**Problem:** MPesa cannot reach your server
**Solution:** 
- Ensure HTTPS is enabled
- Test URL accessibility: `curl https://yourapp.com/mpesa/c2b/confirmation`
- Check firewall settings

### 2. Payment Matching Issues

**Problem:** Cannot match payments to sales
**Solution:**
- Use reference numbers
- Match by amount and time window
- Handle multiple payments of same amount

### 3. Timeout Issues

**Problem:** Customer pays but system doesn't update
**Solution:**
- Implement retry mechanism
- Manual payment verification
- Customer support process

## Costs and Fees

### MPesa Business Costs

1. **Till Number Registration:** Free
2. **Transaction Fees:** 
   - Customer pays standard MPesa rates
   - You receive full amount minus small processing fee
3. **API Access:** Free for approved developers
4. **Monthly Statement:** Available via MPesa portal

### Development Costs

1. **SSL Certificate:** $10-50/year (or free with Let's Encrypt)
2. **Server Hosting:** $10-50/month
3. **Development Time:** 2-4 weeks for full integration

## Going Live Checklist

### Technical Readiness
- [ ] SSL certificate installed and working
- [ ] Callback URLs accessible from internet
- [ ] Database backups configured
- [ ] Error logging implemented
- [ ] Transaction monitoring setup

### MPesa Readiness  
- [ ] Production credentials received
- [ ] Callback URLs registered with Safaricom
- [ ] Till numbers activated for all shops
- [ ] Test transactions completed successfully

### Business Readiness
- [ ] Staff trained on MPesa payments
- [ ] Customer instructions prepared
- [ ] Support procedures established
- [ ] Reconciliation process defined

Your current Comolor POS system already has a solid MPesa integration foundation. The multi-tenant architecture properly handles different shops with their own till numbers, and the payment processing flow is well-designed for real-world usage.