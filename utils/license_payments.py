"""
License Payment Utilities
Handles license payments to super admin's configured payment method (till or phone)
"""

from models import SystemSettings, Shop, LicensePayment, MpesaTransaction
from app import db
from datetime import datetime, timedelta

def get_license_payment_config():
    """Get super admin's license payment configuration"""
    payment_type = get_system_setting('license_payment_type', 'phone')
    payment_number = get_system_setting('license_payment_number', '')
    payment_name = get_system_setting('license_payment_name', 'Super Admin')
    
    return {
        'type': payment_type,  # 'phone' or 'till'
        'number': payment_number,
        'name': payment_name
    }

def get_system_setting(key, default_value=''):
    """Get system setting by key"""
    setting = SystemSettings.query.filter_by(key=key).first()
    return setting.value if setting else default_value

def is_license_payment(mpesa_data):
    """Check if MPesa transaction is a license payment"""
    config = get_license_payment_config()
    
    if not config['number']:
        return False
    
    # Check if payment was sent to configured license payment number
    if config['type'] == 'phone':
        # For phone payments, check if it's sent TO the phone number (C2B)
        return mpesa_data.get('MSISDN') == config['number']
    else:
        # For till payments, check if payment was sent to the till
        return mpesa_data.get('BusinessShortCode') == config['number']

def process_license_payment(mpesa_data):
    """Process license payment from MPesa transaction"""
    config = get_license_payment_config()
    
    if not is_license_payment(mpesa_data):
        return False
    
    # Extract payment details
    transaction_id = mpesa_data.get('TransID')
    amount = float(mpesa_data.get('TransAmount', 0))
    customer_phone = mpesa_data.get('MSISDN')
    bill_ref = mpesa_data.get('BillRefNumber', '').upper()
    
    # Check if already processed
    existing = MpesaTransaction.query.filter_by(transaction_id=transaction_id).first()
    if existing:
        return False
    
    # Create MPesa transaction record
    transaction = MpesaTransaction(
        transaction_type='license',
        transaction_id=transaction_id,
        bill_ref_number=bill_ref,
        amount=amount,
        msisdn=customer_phone,
        first_name=mpesa_data.get('FirstName', ''),
        middle_name=mpesa_data.get('MiddleName', ''),
        last_name=mpesa_data.get('LastName', ''),
        transaction_time=parse_mpesa_time(mpesa_data.get('TransTime')),
        is_processed=False
    )
    db.session.add(transaction)
    
    # Try to auto-process if we can identify the shop
    shop = None
    
    # Method 1: Check if bill reference contains shop ID
    if bill_ref.startswith('SHOP'):
        try:
            shop_id = int(bill_ref.replace('SHOP', ''))
            shop = Shop.query.get(shop_id)
        except ValueError:
            pass
    
    # Method 2: Check if bill reference is a till number
    if not shop and bill_ref:
        shop = Shop.query.filter_by(till_number=bill_ref).first()
    
    # Method 3: Check if customer phone matches shop owner phone
    if not shop and customer_phone:
        shop = Shop.query.filter_by(phone=customer_phone).first()
    
    if shop:
        # Auto-approve license payment
        approve_license_payment(transaction, shop)
    else:
        # Mark for manual review
        transaction.shop_id = None
    
    db.session.commit()
    return True

def approve_license_payment(transaction, shop):
    """Approve license payment and activate shop"""
    license_amount = float(get_system_setting('license_amount', '3000'))
    
    # Calculate license period based on amount paid
    months = max(1, int(transaction.amount / license_amount))
    
    license_start = datetime.utcnow()
    license_end = license_start + timedelta(days=30 * months)
    
    # Create license payment record
    payment = LicensePayment(
        shop_id=shop.id,
        amount=transaction.amount,
        mpesa_transaction_id=transaction.transaction_id,
        payment_date=transaction.transaction_time,
        license_start=license_start,
        license_end=license_end,
        status='approved'
    )
    
    # Update shop
    shop.license_expires = license_end
    shop.is_active = True
    
    # Mark transaction as processed
    transaction.is_processed = True
    transaction.shop_id = shop.id
    
    db.session.add(payment)
    return payment

def get_license_payment_instructions(shop_id):
    """Get payment instructions for shop license"""
    config = get_license_payment_config()
    license_amount = get_system_setting('license_amount', '3000')
    
    if not config['number']:
        return {
            'error': 'License payment not configured. Contact system administrator.'
        }
    
    shop = Shop.query.get(shop_id)
    if not shop:
        return {'error': 'Shop not found'}
    
    # Generate reference for easier identification
    reference = f"SHOP{shop_id}"
    
    if config['type'] == 'phone':
        instructions = {
            'type': 'phone',
            'number': config['number'],
            'name': config['name'],
            'amount': license_amount,
            'reference': reference,
            'instructions': [
                f"1. Go to M-Pesa menu on your phone",
                f"2. Select 'Send Money'",
                f"3. Enter phone number: {config['number']}",
                f"4. Enter amount: KES {license_amount}",
                f"5. For reference/reason: {reference}",
                f"6. Complete with your M-Pesa PIN"
            ],
            'ussd': f"*150*01*{config['number']}*{license_amount}#",
            'note': "Payment will be processed automatically once received"
        }
    else:
        instructions = {
            'type': 'till',
            'number': config['number'],
            'name': config['name'],
            'amount': license_amount,
            'reference': reference,
            'instructions': [
                f"1. Go to M-Pesa menu on your phone",
                f"2. Select 'Lipa na M-Pesa'",
                f"3. Select 'Buy Goods and Services'",
                f"4. Enter till number: {config['number']}",
                f"5. Enter amount: KES {license_amount}",
                f"6. For reference: {reference}",
                f"7. Complete with your M-Pesa PIN"
            ],
            'ussd': f"*150*01*{config['number']}*{license_amount}#",
            'note': "Payment will be processed automatically once received"
        }
    
    return instructions

def parse_mpesa_time(time_str):
    """Parse MPesa timestamp format"""
    if not time_str:
        return datetime.utcnow()
    
    try:
        # MPesa format: 20191122063845 (YYYYMMDDHHMMSS)
        return datetime.strptime(time_str, '%Y%m%d%H%M%S')
    except ValueError:
        return datetime.utcnow()

def get_pending_license_payments():
    """Get all pending license payments for super admin review"""
    return MpesaTransaction.query.filter_by(
        transaction_type='license',
        is_processed=False
    ).order_by(MpesaTransaction.created_at.desc()).all()

def get_license_payment_stats():
    """Get license payment statistics"""
    total_payments = LicensePayment.query.filter_by(status='approved').count()
    total_revenue = db.session.query(db.func.sum(LicensePayment.amount)).filter_by(status='approved').scalar() or 0
    pending_payments = get_pending_license_payments()
    
    return {
        'total_payments': total_payments,
        'total_revenue': float(total_revenue),
        'pending_count': len(pending_payments),
        'pending_amount': sum(float(p.amount) for p in pending_payments)
    }

def manual_license_approval(transaction_id, shop_id):
    """Manually approve license payment for specific shop"""
    transaction = MpesaTransaction.query.get(transaction_id)
    shop = Shop.query.get(shop_id)
    
    if not transaction or not shop or transaction.is_processed:
        return False
    
    payment = approve_license_payment(transaction, shop)
    db.session.commit()
    
    return payment