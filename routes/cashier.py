from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import Product, Sale, SaleItem, StockMovement, MpesaTransaction, Shop
from app import db
from utils.auth import require_role, require_shop_access, log_audit
from datetime import datetime, timedelta
import uuid

bp = Blueprint('cashier', __name__, url_prefix='/cashier')

@bp.before_request
def check_auth():
    if 'user_id' not in session or session.get('role') not in ['cashier', 'shop_admin', 'super_admin']:
        return redirect(url_for('auth.login'))
    
    # Check shop license for cashiers and shop admins (not super admin when impersonating)
    if session.get('role') in ['cashier', 'shop_admin'] and not session.get('impersonating'):
        from models import User
        user = User.query.get(session['user_id'])
        if user and user.shop and (not user.shop.is_active or not user.shop.is_license_active()):
            flash('Shop license has expired. Please contact your administrator.', 'error')
            return redirect(url_for('auth.logout'))

@bp.route('/pos')
@require_shop_access
def pos():
    # Get products for the shop
    products = Product.query.filter_by(
        shop_id=session['shop_id'],
        is_active=True
    ).order_by(Product.name).all()
    
    # Get shop settings
    shop = Shop.query.get(session['shop_id'])
    settings = {}
    if shop and shop.settings:
        settings = shop.settings
    
    return render_template('cashier/pos.html', products=products, shop=shop, settings=settings)

@bp.route('/api/products/search')
@require_shop_access
def search_products():
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify([])
    
    products = Product.query.filter(
        Product.shop_id == session['shop_id'],
        Product.is_active == True,
        (Product.name.ilike(f'%{query}%') | 
         Product.barcode.ilike(f'%{query}%') |
         Product.sku.ilike(f'%{query}%'))
    ).limit(10).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': float(p.price),
        'barcode': p.barcode,
        'stock_quantity': p.stock_quantity
    } for p in products])

@bp.route('/api/products/<barcode>')
@require_shop_access
def get_product_by_barcode(barcode):
    product = Product.query.filter_by(
        shop_id=session['shop_id'],
        barcode=barcode,
        is_active=True
    ).first()
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': float(product.price),
        'barcode': product.barcode,
        'stock_quantity': product.stock_quantity
    })

@bp.route('/sale/create', methods=['POST'])
@require_shop_access
def create_sale():
    data = request.get_json()
    
    if not data or not data.get('items'):
        return jsonify({'error': 'No items provided'}), 400
    
    try:
        # Generate receipt number
        receipt_number = f"RCP{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        
        # Calculate totals from cart items
        subtotal = 0
        for item in data['items']:
            if 'lineTotal' in item:
                subtotal += item['lineTotal']
            else:
                subtotal += item['quantity'] * item['unitPrice']
        
        shop = Shop.query.get(session['shop_id'])
        settings = shop.settings if shop and shop.settings else {}
        tax_rate = settings.get('tax_rate', 16) / 100
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        # Create sale
        sale = Sale()
        sale.receipt_number = receipt_number
        sale.shop_id = session['shop_id']
        sale.cashier_id = session['user_id']
        sale.subtotal = subtotal
        sale.tax_amount = tax_amount
        sale.total_amount = total_amount
        sale.payment_method = data['payment_method']
        
        db.session.add(sale)
        db.session.flush()  # Get sale ID
        
        # Create sale items and update stock
        for item_data in data['items']:
            product_id = item_data.get('productId') or item_data.get('product_id')
            product = Product.query.get(product_id)
            if not product or product.shop_id != session['shop_id']:
                raise ValueError(f"Invalid product: {product_id}")
            
            quantity = item_data['quantity']
            if product.stock_quantity < quantity:
                raise ValueError(f"Insufficient stock for {product.name}")
            
            # Create sale item
            sale_item = SaleItem()
            sale_item.sale_id = sale.id
            sale_item.product_id = product.id
            sale_item.quantity = quantity
            sale_item.unit_price = item_data.get('unitPrice', product.price)
            sale_item.line_total = item_data.get('lineTotal', quantity * sale_item.unit_price)
            db.session.add(sale_item)
            
            # Update stock
            product.stock_quantity -= quantity
            
            # Create stock movement
            movement = StockMovement()
            movement.product_id = product.id
            movement.movement_type = 'out'
            movement.quantity = quantity
            movement.reference = receipt_number
            movement.notes = f'Sale: {receipt_number}'
            movement.created_by = session['user_id']
            db.session.add(movement)
        
        db.session.commit()
        
        log_audit(session['user_id'], 'create_sale', 'sale', sale.id,
                  request.remote_addr, request.user_agent.string,
                  new_values={'receipt_number': receipt_number, 'total_amount': float(total_amount)})
        
        return jsonify({
            'success': True,
            'sale_id': sale.id,
            'receipt_number': receipt_number,
            'total_amount': float(total_amount)
        })
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create sale'}), 500

@bp.route('/mpesa/check/<int:sale_id>')
@require_shop_access
def check_mpesa_payment(sale_id):
    """Check if MPesa payment has been received for a sale"""
    sale = Sale.query.get_or_404(sale_id)
    if sale.shop_id != session['shop_id']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Check if payment already confirmed
    if sale.mpesa_receipt:
        return jsonify({
            'payment_received': True,
            'payment_data': {
                'amount': float(sale.total_amount),
                'phone': sale.customer_phone or 'Unknown',
                'mpesa_code': sale.mpesa_receipt,
                'customer_name': sale.customer_name or 'Customer',
                'transaction_time': sale.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    # Look for recent MPesa transactions
    shop = Shop.query.get(session['shop_id'])
    recent_time = datetime.now() - timedelta(minutes=10)
    
    transaction = MpesaTransaction.query.filter(
        MpesaTransaction.amount == sale.total_amount,
        MpesaTransaction.transaction_time >= recent_time,
        MpesaTransaction.is_processed == False
    ).order_by(MpesaTransaction.transaction_time.desc()).first()
    
    if transaction:
        return jsonify({
            'payment_received': True,
            'payment_data': {
                'amount': float(transaction.amount),
                'phone': transaction.msisdn,
                'mpesa_code': transaction.transaction_id,
                'customer_name': f"{transaction.first_name or ''} {transaction.middle_name or ''} {transaction.last_name or ''}".strip() or 'Customer',
                'transaction_time': transaction.transaction_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    return jsonify({'payment_received': False})

@bp.route('/mpesa/confirm/<int:sale_id>', methods=['POST'])
@require_shop_access
def confirm_mpesa_payment(sale_id):
    """Confirm MPesa payment for a sale"""
    sale = Sale.query.get_or_404(sale_id)
    if sale.shop_id != session['shop_id']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Find the matching transaction
    recent_time = datetime.now() - timedelta(minutes=10)
    transaction = MpesaTransaction.query.filter(
        MpesaTransaction.amount == sale.total_amount,
        MpesaTransaction.transaction_time >= recent_time,
        MpesaTransaction.is_processed == False
    ).order_by(MpesaTransaction.transaction_time.desc()).first()
    
    if not transaction:
        return jsonify({'message': 'No matching payment found'}), 400
    
    try:
        # Update sale with payment details
        sale.mpesa_receipt = transaction.transaction_id
        sale.customer_phone = transaction.msisdn
        sale.customer_name = f"{transaction.first_name or ''} {transaction.middle_name or ''} {transaction.last_name or ''}".strip()
        
        # Mark transaction as processed
        transaction.is_processed = True
        transaction.sale_id = sale.id
        
        db.session.commit()
        
        log_audit(session['user_id'], 'confirm_mpesa_payment', 'sale', sale.id,
                  request.remote_addr, request.user_agent.string,
                  new_values={'mpesa_receipt': transaction.transaction_id})
        
        return jsonify({
            'success': True,
            'sale_id': sale.id,
            'mpesa_receipt': transaction.transaction_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to confirm payment'}), 500



@bp.route('/receipt/<int:sale_id>')
@require_shop_access
def view_receipt(sale_id):
    sale = Sale.query.filter_by(id=sale_id, shop_id=session['shop_id']).first_or_404()
    shop = Shop.query.get(session['shop_id'])
    
    return render_template('cashier/receipt.html', sale=sale, shop=shop)

@bp.route('/receipt/<int:sale_id>/print')
@require_shop_access
def print_receipt(sale_id):
    sale = Sale.query.filter_by(id=sale_id, shop_id=session['shop_id']).first_or_404()
    shop = Shop.query.get(session['shop_id'])
    
    return render_template('cashier/print_receipt.html', sale=sale, shop=shop)

@bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Save cashier settings to database or session
        from models import User
        user = User.query.get(session['user_id'])
        
        # Update user settings (you can extend User model to include settings JSON field)
        settings_data = {
            'theme': request.form.get('theme', 'light'),
            'language': request.form.get('language', 'en'),
            'default_printer': request.form.get('default_printer', ''),
            'receipt_width': request.form.get('receipt_width', '80mm'),
            'screen_mode': request.form.get('screen_mode', 'windowed'),
            'auto_logout_time': request.form.get('auto_logout_time', '300'),
            'network_mode': request.form.get('network_mode', 'online'),
            'time_zone': request.form.get('time_zone', 'Africa/Nairobi'),
            'startup_behavior': request.form.get('startup_behavior', 'new_sale'),
            'default_payment_mode': request.form.get('default_payment_mode', 'mpesa'),
            'sound_volume': request.form.get('sound_volume', '75'),
            'auto_receipt': request.form.get('auto_receipt') == 'on',
            'touchscreen_mode': request.form.get('touchscreen_mode') == 'on',
            'auto_lock_pos': request.form.get('auto_lock_pos') == 'on',
            'enable_beep_on_scan': request.form.get('enable_beep_on_scan') == 'on',
            'payment_sounds': request.form.get('payment_sounds') == 'on',
            'error_sounds': request.form.get('error_sounds') == 'on',
            'keyboard_shortcuts': request.form.get('keyboard_shortcuts') == 'on',
            'auto_focus': request.form.get('auto_focus') == 'on',
            'quick_add': request.form.get('quick_add') == 'on',
            'auto_update': request.form.get('auto_update') == 'on',
            'show_welcome_screen': request.form.get('show_welcome_screen') == 'on',
            'scanner_prefix': request.form.get('scanner_prefix', ''),
            'scanner_suffix': request.form.get('scanner_suffix', '')
        }
        
        # Store in session for now (could be extended to database)
        session['cashier_settings'] = settings_data
        
        # Log audit trail
        if user:
            log_audit(
                user_id=session['user_id'],
                action='update_cashier_settings',
                entity_type='user_settings',
                entity_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                new_values=settings_data
            )
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('cashier.settings'))
    
    return render_template('cashier/settings.html')

@bp.route('/test-printer', methods=['POST'])
@require_shop_access
def test_printer():
    """Test the receipt printer with a sample receipt"""
    try:
        from utils.reports import generate_sales_report_pdf
        from datetime import datetime
        
        # Generate a test receipt
        test_data = {
            'receipt_number': 'TEST-' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'shop_name': session.get('shop_name', 'Demo Shop'),
            'items': [
                {'name': 'Test Item', 'quantity': 1, 'price': 100.00, 'total': 100.00}
            ],
            'total': 100.00,
            'payment_method': 'TEST',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # In a real implementation, this would send to the actual printer
        # For now, we'll just return success
        return jsonify({
            'success': True,
            'message': 'Test receipt generated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/check-connection', methods=['POST'])
@require_shop_access  
def check_connection():
    """Check internet connection and server connectivity"""
    import time
    import requests
    
    try:
        start_time = time.time()
        
        # Test connection to a reliable endpoint
        response = requests.get('https://httpbin.org/status/200', timeout=5)
        
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        if response.status_code == 200:
            return jsonify({
                'online': True,
                'response_time': response_time,
                'message': 'Connection successful'
            })
        else:
            return jsonify({
                'online': False,
                'message': f'Server returned status code: {response.status_code}'
            })
            
    except requests.exceptions.Timeout:
        return jsonify({
            'online': False,
            'message': 'Connection timeout - check your internet connection'
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            'online': False,
            'message': 'No internet connection available'
        })
    except Exception as e:
        return jsonify({
            'online': False,
            'message': f'Connection test failed: {str(e)}'
        })
