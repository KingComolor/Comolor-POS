from flask import Blueprint, request, jsonify, render_template
from models import MpesaTransaction, Shop, Sale, LicensePayment
from app import db
from datetime import datetime, timedelta
import logging
from utils.mpesa import mpesa_api
from utils.license_payments import process_license_payment, is_license_payment, get_license_payment_instructions

bp = Blueprint('mpesa', __name__, url_prefix='/mpesa')

@bp.route('/c2b/confirmation', methods=['POST'])
def c2b_confirmation():
    """Handle MPesa C2B confirmation callback with webhook validation"""
    try:
        # Get raw request data for signature validation
        raw_data = request.get_data(as_text=True)
        signature = request.headers.get('X-Mpesa-Signature', '')
        
        # Validate webhook signature for security
        if signature and not mpesa_api.validate_webhook_signature(raw_data, signature):
            logging.error("Invalid webhook signature")
            return jsonify({"ResultCode": 1, "ResultDesc": "Invalid signature"}), 401
        
        data = request.get_json()
        
        if not data:
            logging.error("No data received in MPesa callback")
            return jsonify({"ResultCode": 1, "ResultDesc": "No data received"}), 400
        
        # Process payment using enhanced MPesa API
        payment_result = mpesa_api.process_c2b_payment(data)
        
        if not payment_result['success']:
            logging.error(f"Payment processing failed: {payment_result.get('error')}")
            return jsonify({"ResultCode": 1, "ResultDesc": "Payment processing failed"}), 400
        
        # Check if transaction already exists
        existing = MpesaTransaction.query.filter_by(
            transaction_id=payment_result['transaction_id']
        ).first()
        
        if existing:
            logging.info(f"Transaction {payment_result['transaction_id']} already exists")
            return jsonify({"ResultCode": 0, "ResultDesc": "Transaction already processed"})
        
        # Parse transaction time
        transaction_time = datetime.strptime(payment_result['timestamp'], '%Y%m%d%H%M%S')
        
        # Create transaction record
        transaction = MpesaTransaction(
            transaction_type=payment_result['payment_type'],
            transaction_id=payment_result['transaction_id'],
            bill_ref_number=payment_result['reference'],
            amount=payment_result['amount'],
            msisdn=payment_result['phone'],
            first_name=payment_result['customer_name'].split()[0] if payment_result['customer_name'] else '',
            middle_name=' '.join(payment_result['customer_name'].split()[1:-1]) if len(payment_result['customer_name'].split()) > 2 else '',
            last_name=payment_result['customer_name'].split()[-1] if len(payment_result['customer_name'].split()) > 1 else '',
            transaction_time=transaction_time,
            is_processed=False
        )
        
        # Check if this is a license payment first
        if is_license_payment(data):
            # Process license payment using new system
            license_processed = process_license_payment(data)
            if license_processed:
                logging.info(f"License payment processed: {payment_result['transaction_id']}")
                return jsonify({"ResultCode": 0, "ResultDesc": "License payment processed"})
        
        # Process based on payment type
        if payment_result['payment_type'] == 'license':
            transaction.shop_id = None  # License payments not tied to specific shop initially
                
        elif payment_result['payment_type'] == 'sale':
            # Handle sale payment to shop till
            shop = Shop.query.filter_by(till_number=payment_result['business_code']).first()
            if shop:
                transaction.shop_id = shop.id
                # Try to match with pending sale
                pending_sale = Sale.query.filter_by(
                    shop_id=shop.id,
                    payment_method='mpesa',
                    mpesa_receipt=None,
                    status='completed'
                ).order_by(Sale.created_at.desc()).first()
                
                if pending_sale and abs(float(pending_sale.total_amount) - payment_result['amount']) < 0.01:
                    # Match found - update sale with MPesa receipt
                    pending_sale.mpesa_receipt = payment_result['transaction_id']
                    pending_sale.customer_phone = payment_result['phone']
                    pending_sale.customer_name = payment_result['customer_name']
                    transaction.sale_id = pending_sale.id
                    transaction.is_processed = True
                    
                    logging.info(f"Matched MPesa payment {payment_result['transaction_id']} to sale {pending_sale.id}")
        
        db.session.add(transaction)
        db.session.commit()
        
        logging.info(f"MPesa transaction processed: {payment_result['transaction_id']}, Amount: {payment_result['amount']}, Type: {payment_result['payment_type']}")
        
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"})
        
    except Exception as e:
        logging.error(f"Error processing MPesa callback: {str(e)}")
        db.session.rollback()
        return jsonify({"ResultCode": 1, "ResultDesc": "Internal server error"}), 500

@bp.route('/c2b/validation', methods=['POST'])
def c2b_validation():
    """Handle MPesa C2B validation callback"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"ResultCode": 1, "ResultDesc": "No data received"}), 400
        
        amount = float(data.get('TransAmount', 0))
        bill_ref_number = data.get('BillRefNumber', '')
        
        # Validate bill reference number
        if bill_ref_number.startswith('TILL'):
            # Check if shop exists with this till number
            shop = Shop.query.filter_by(till_number=bill_ref_number).first()
            if not shop:
                return jsonify({"ResultCode": 1, "ResultDesc": "Invalid Till Number"})
        
        # Additional validation logic can be added here
        # For now, accept all transactions
        
        logging.info(f"MPesa validation passed: Bill Ref: {bill_ref_number}, Amount: {amount}")
        
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"})
        
    except Exception as e:
        logging.error(f"Error in MPesa validation: {str(e)}")
        return jsonify({"ResultCode": 1, "ResultDesc": "Validation failed"}), 500

@bp.route('/c2b/timeout', methods=['POST'])
def c2b_timeout():
    """Handle MPesa C2B timeout callback"""
    try:
        data = request.get_json()
        logging.warning(f"MPesa timeout received: {data}")
        
        return jsonify({"ResultCode": 0, "ResultDesc": "Timeout received"})
        
    except Exception as e:
        logging.error(f"Error handling MPesa timeout: {str(e)}")
        return jsonify({"ResultCode": 1, "ResultDesc": "Error handling timeout"}), 500

@bp.route('/payment/status/<int:sale_id>')
def get_payment_status(sale_id):
    """Get real-time payment status for a sale"""
    try:
        sale = Sale.query.get_or_404(sale_id)
        
        # Check if payment already received
        if sale.mpesa_receipt:
            return jsonify({
                'status': 'completed',
                'mpesa_receipt': sale.mpesa_receipt,
                'customer_phone': sale.customer_phone,
                'customer_name': sale.customer_name,
                'amount': float(sale.total_amount)
            })
        
        # Check for recent transactions matching this sale
        recent_transactions = MpesaTransaction.query.filter(
            MpesaTransaction.shop_id == sale.shop_id,
            MpesaTransaction.transaction_time >= sale.created_at - timedelta(minutes=5),
            MpesaTransaction.amount == sale.total_amount,
            MpesaTransaction.is_processed == False
        ).order_by(MpesaTransaction.transaction_time.desc()).all()
        
        for transaction in recent_transactions:
            # Match transaction to sale
            sale.mpesa_receipt = transaction.transaction_id
            sale.customer_phone = transaction.msisdn
            sale.customer_name = f"{transaction.first_name} {transaction.middle_name} {transaction.last_name}".strip()
            transaction.sale_id = sale.id
            transaction.is_processed = True
            
            db.session.commit()
            
            return jsonify({
                'status': 'completed',
                'mpesa_receipt': sale.mpesa_receipt,
                'customer_phone': sale.customer_phone,
                'customer_name': sale.customer_name,
                'amount': float(sale.total_amount)
            })
        
        # No payment found yet
        return jsonify({
            'status': 'pending',
            'amount': float(sale.total_amount),
            'till_number': sale.shop.till_number if sale.shop else None
        })
        
    except Exception as e:
        logging.error(f"Error checking payment status: {e}")
        return jsonify({'error': 'Failed to check payment status'}), 500

@bp.route('/payment/simulate', methods=['POST'])
def simulate_payment():
    """Simulate MPesa payment for testing"""
    try:
        data = request.get_json()
        sale_id = data.get('sale_id')
        phone = data.get('phone', '254712345678')
        
        sale = Sale.query.get_or_404(sale_id)
        
        if not sale.shop or not sale.shop.till_number:
            return jsonify({'error': 'Shop till number not configured'}), 400
        
        # Simulate C2B payment
        success = mpesa_api.simulate_c2b_payment(
            amount=float(sale.total_amount),
            msisdn=phone,
            bill_ref_number=sale.shop.till_number
        )
        
        if success:
            return jsonify({'status': 'success', 'message': 'Payment simulation initiated'})
        else:
            return jsonify({'error': 'Payment simulation failed'}), 500
            
    except Exception as e:
        logging.error(f"Error simulating payment: {e}")
        return jsonify({'error': 'Simulation failed'}), 500

@bp.route('/register/shop/<int:shop_id>')
def register_shop_webhook(shop_id):
    """Register webhook URLs for a specific shop"""
    try:
        shop = Shop.query.get_or_404(shop_id)
        
        if not shop.till_number:
            return jsonify({'error': 'Shop till number not configured'}), 400
        
        # Get base URL from request
        base_url = request.url_root.rstrip('/')
        confirmation_url = f"{base_url}/mpesa/c2b/confirmation"
        validation_url = f"{base_url}/mpesa/c2b/validation"
        
        # Register URLs with MPesa
        success = mpesa_api.register_c2b_urls(
            shop.till_number,
            confirmation_url,
            validation_url
        )
        
        if success:
            logging.info(f"Registered webhook URLs for shop {shop.name} (Till: {shop.till_number})")
            return jsonify({'status': 'success', 'message': 'Webhook URLs registered'})
        else:
            return jsonify({'error': 'Failed to register webhook URLs'}), 500
            
    except Exception as e:
        logging.error(f"Error registering webhook: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@bp.route('/pay-license/<int:shop_id>')
def pay_license(shop_id):
    """Display license payment instructions for a shop"""
    instructions = get_license_payment_instructions(shop_id)
    
    if 'error' in instructions:
        return render_template('error.html', 
                             title='Payment Configuration Error',
                             message=instructions['error']), 400
    
    return render_template('mpesa/pay_license.html', 
                         instructions=instructions, 
                         shop_id=shop_id)

@bp.route('/health')
def health_check():
    """Health check endpoint for MPesa integration"""
    return jsonify({
        "status": "healthy", 
        "service": "Comolor POS MPesa Integration",
        "environment": "production"
    })
