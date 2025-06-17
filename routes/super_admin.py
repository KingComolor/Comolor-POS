from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash
from models import User, Shop, LicensePayment, MpesaTransaction, AuditLog, SystemSettings, Sale, Product
from app import db
from utils.auth import require_role, log_audit
from datetime import datetime, timedelta
from sqlalchemy import func, desc

bp = Blueprint('super_admin', __name__, url_prefix='/super-admin')

@bp.before_request
def check_auth():
    if 'user_id' not in session or session.get('role') != 'super_admin':
        return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@require_role('super_admin')
def dashboard():
    # Statistics
    total_shops = Shop.query.count()
    active_shops = Shop.query.filter_by(is_active=True).count()
    total_users = User.query.count()
    
    # Revenue this month
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = db.session.query(func.sum(LicensePayment.amount)).filter(
        LicensePayment.created_at >= current_month,
        LicensePayment.status == 'approved'
    ).scalar() or 0
    
    # Recent MPesa transactions
    recent_transactions = MpesaTransaction.query.filter_by(transaction_type='license').order_by(desc(MpesaTransaction.created_at)).limit(10).all()
    
    # Shops with expiring licenses (next 30 days)
    expiring_soon = datetime.now() + timedelta(days=30)
    expiring_licenses = Shop.query.filter(
        Shop.license_expires.between(datetime.now(), expiring_soon)
    ).all()
    
    # Recent audit logs
    recent_logs = AuditLog.query.order_by(desc(AuditLog.created_at)).limit(20).all()
    
    return render_template('super_admin/dashboard.html',
                         total_shops=total_shops,
                         active_shops=active_shops,
                         total_users=total_users,
                         monthly_revenue=monthly_revenue,
                         recent_transactions=recent_transactions,
                         expiring_licenses=expiring_licenses,
                         recent_logs=recent_logs)

@bp.route('/shops')
@require_role('super_admin')
def shops():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Shop.query
    if search:
        query = query.filter(
            (Shop.name.ilike(f'%{search}%')) |
            (Shop.owner_name.ilike(f'%{search}%')) |
            (Shop.email.ilike(f'%{search}%'))
        )
    
    shops = query.order_by(desc(Shop.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('super_admin/shops.html', shops=shops, search=search)

@bp.route('/shops/<int:shop_id>/toggle-status')
@require_role('super_admin')
def toggle_shop_status(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    shop.is_active = not shop.is_active
    db.session.commit()
    
    log_audit(session['user_id'], 'toggle_shop_status', 'shop', shop_id, 
              request.remote_addr, request.user_agent.string,
              old_values={'is_active': not shop.is_active},
              new_values={'is_active': shop.is_active})
    
    status = 'activated' if shop.is_active else 'deactivated'
    flash(f'Shop {shop.name} has been {status}', 'success')
    return redirect(url_for('super_admin.shops'))

@bp.route('/shops/<int:shop_id>/edit', methods=['GET', 'POST'])
@require_role('super_admin')
def edit_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    
    if request.method == 'POST':
        old_values = {
            'name': shop.name,
            'owner_name': shop.owner_name,
            'email': shop.email,
            'phone': shop.phone,
            'address': shop.address,
            'till_number': shop.till_number
        }
        
        shop.name = request.form['name']
        shop.owner_name = request.form['owner_name']
        shop.email = request.form['email']
        shop.phone = request.form['phone']
        shop.address = request.form['address']
        shop.till_number = request.form['till_number']
        
        db.session.commit()
        
        log_audit(session['user_id'], 'edit_shop', 'shop', shop_id,
                  request.remote_addr, request.user_agent.string,
                  old_values=old_values,
                  new_values={
                      'name': shop.name,
                      'owner_name': shop.owner_name,
                      'email': shop.email,
                      'phone': shop.phone,
                      'address': shop.address,
                      'till_number': shop.till_number
                  })
        
        flash('Shop updated successfully', 'success')
        return redirect(url_for('super_admin.shops'))
    
    return render_template('super_admin/edit_shop.html', shop=shop)

@bp.route('/shops/<int:shop_id>/login-as')
@require_role('super_admin')
def login_as_shop_admin(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    shop_admin = User.query.filter_by(shop_id=shop_id, role='shop_admin').first()
    
    if not shop_admin:
        flash('No shop admin found for this shop', 'error')
        return redirect(url_for('super_admin.shops'))
    
    # Store original user ID for returning
    session['original_user_id'] = session['user_id']
    session['impersonating'] = True
    
    # Switch to shop admin session
    session['user_id'] = shop_admin.id
    session['username'] = shop_admin.username
    session['role'] = shop_admin.role
    session['shop_id'] = shop_admin.shop_id
    
    log_audit(session['original_user_id'], 'impersonate_user', 'user', shop_admin.id,
              request.remote_addr, request.user_agent.string)
    
    flash(f'Now logged in as {shop_admin.username} ({shop.name})', 'info')
    return redirect(url_for('shop_admin.dashboard'))

@bp.route('/return-to-super-admin')
@require_role('shop_admin')
def return_to_super_admin():
    if not session.get('impersonating'):
        return redirect(url_for('auth.login'))
    
    original_user = User.query.get(session['original_user_id'])
    if not original_user or original_user.role != 'super_admin':
        return redirect(url_for('auth.login'))
    
    # Return to super admin session
    session['user_id'] = original_user.id
    session['username'] = original_user.username
    session['role'] = original_user.role
    session['shop_id'] = None
    session.pop('original_user_id', None)
    session.pop('impersonating', None)
    
    flash('Returned to Super Admin view', 'info')
    return redirect(url_for('super_admin.dashboard'))

@bp.route('/users')
@require_role('super_admin')
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    
    query = User.query.join(Shop, User.shop_id == Shop.id, isouter=True)
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (Shop.name.ilike(f'%{search}%'))
        )
    
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    users = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('super_admin/users.html', users=users, search=search, role_filter=role_filter)

@bp.route('/users/<int:user_id>/toggle-status')
@require_role('super_admin')
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'super_admin':
        flash('Cannot deactivate super admin users', 'error')
        return redirect(url_for('super_admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    log_audit(session['user_id'], 'toggle_user_status', 'user', user_id,
              request.remote_addr, request.user_agent.string,
              old_values={'is_active': not user.is_active},
              new_values={'is_active': user.is_active})
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}', 'success')
    return redirect(url_for('super_admin.users'))

@bp.route('/licenses')
@require_role('super_admin')
def licenses():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = LicensePayment.query.join(Shop).order_by(desc(LicensePayment.created_at))
    
    if status_filter:
        query = query.filter(LicensePayment.status == status_filter)
    
    payments = query.paginate(page=page, per_page=20, error_out=False)
    
    # Pending license payments from MPesa transactions
    pending_mpesa = MpesaTransaction.query.filter_by(
        transaction_type='license',
        is_processed=False
    ).order_by(desc(MpesaTransaction.created_at)).all()
    
    return render_template('super_admin/licenses.html', payments=payments, 
                         pending_mpesa=pending_mpesa, status_filter=status_filter)

@bp.route('/licenses/approve-mpesa/<int:transaction_id>')
@require_role('super_admin')
def approve_mpesa_license(transaction_id):
    transaction = MpesaTransaction.query.get_or_404(transaction_id)
    
    if transaction.is_processed:
        flash('Transaction already processed', 'error')
        return redirect(url_for('super_admin.licenses'))
    
    # Find shop by till number from bill_ref_number
    shop = Shop.query.filter_by(till_number=transaction.bill_ref_number).first()
    if not shop:
        flash('Shop not found for this transaction', 'error')
        return redirect(url_for('super_admin.licenses'))
    
    # Create license payment
    license_start = datetime.now()
    license_end = license_start + timedelta(days=30)  # 30-day license
    
    payment = LicensePayment(
        shop_id=shop.id,
        amount=transaction.amount,
        mpesa_transaction_id=transaction.transaction_id,
        payment_date=transaction.transaction_time,
        license_start=license_start,
        license_end=license_end,
        approved_by=session['user_id'],
        status='approved'
    )
    
    # Update shop
    shop.license_expires = license_end
    shop.is_active = True
    
    # Mark transaction as processed
    transaction.is_processed = True
    transaction.shop_id = shop.id
    
    db.session.add(payment)
    db.session.commit()
    
    log_audit(session['user_id'], 'approve_license', 'license_payment', payment.id,
              request.remote_addr, request.user_agent.string,
              new_values={'shop_id': shop.id, 'amount': float(transaction.amount)})
    
    flash(f'License approved for {shop.name}. Valid until {license_end.strftime("%Y-%m-%d")}', 'success')
    return redirect(url_for('super_admin.licenses'))

@bp.route('/settings', methods=['GET', 'POST'])
@require_role('super_admin')
def settings():
    if request.method == 'POST':
        # Update system settings
        settings_data = [
            ('system_name', request.form.get('system_name', 'Comolor POS')),
            ('license_amount', request.form.get('license_amount', '3000')),
            ('default_tax_rate', request.form.get('default_tax_rate', '16')),
            ('mpesa_consumer_key', request.form.get('mpesa_consumer_key', '')),
            ('mpesa_consumer_secret', request.form.get('mpesa_consumer_secret', '')),
            ('mpesa_shortcode', request.form.get('mpesa_shortcode', '')),
            ('mpesa_passkey', request.form.get('mpesa_passkey', '')),
            ('license_payment_type', request.form.get('license_payment_type', 'phone')),
            ('license_payment_number', request.form.get('license_payment_number', '')),
            ('license_payment_name', request.form.get('license_payment_name', 'Super Admin')),
        ]
        
        for key, value in settings_data:
            setting = SystemSettings.query.filter_by(key=key).first()
            if setting:
                setting.value = value
                setting.updated_at = datetime.now()
            else:
                setting = SystemSettings(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
        
        log_audit(session['user_id'], 'update_system_settings', 'system_settings', None,
                  request.remote_addr, request.user_agent.string)
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('super_admin.settings'))
    
    # Load current settings
    settings = {}
    for setting in SystemSettings.query.all():
        settings[setting.key] = setting.value
    
    return render_template('super_admin/settings.html', settings=settings)
