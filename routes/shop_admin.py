from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash
from models import User, Shop, Product, Category, Sale, SaleItem, StockMovement, MpesaTransaction
from app import db
from utils.auth import require_role, require_shop_access, log_audit
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import csv
import io

bp = Blueprint('shop_admin', __name__, url_prefix='/shop-admin')

@bp.before_request
def check_auth():
    if 'user_id' not in session or session.get('role') not in ['shop_admin', 'super_admin']:
        return redirect(url_for('auth.login'))
    
    # Check if shop admin has access to their shop
    if session.get('role') == 'shop_admin' and not session.get('impersonating'):
        user = User.query.get(session['user_id'])
        if not user.shop or not user.shop.is_active or not user.shop.is_license_active:
            flash('Your shop license has expired. Please renew to continue.', 'error')
            return redirect(url_for('auth.logout'))

@bp.route('/dashboard')
@require_shop_access
def dashboard():
    shop_id = session['shop_id']
    
    # Today's sales
    today = datetime.now().date()
    today_sales = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.shop_id == shop_id,
        func.date(Sale.created_at) == today,
        Sale.status == 'completed'
    ).scalar() or 0
    
    # This month's sales
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_sales = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.shop_id == shop_id,
        Sale.created_at >= current_month,
        Sale.status == 'completed'
    ).scalar() or 0
    
    # Top selling products this month
    top_products = db.session.query(
        Product.name,
        func.sum(SaleItem.quantity).label('total_quantity'),
        func.sum(SaleItem.line_total).label('total_revenue')
    ).join(SaleItem).join(Sale).filter(
        Product.shop_id == shop_id,
        Sale.created_at >= current_month,
        Sale.status == 'completed'
    ).group_by(Product.id, Product.name).order_by(desc('total_revenue')).limit(5).all()
    
    # Low stock products
    low_stock_products = Product.query.filter(
        Product.shop_id == shop_id,
        Product.stock_quantity <= Product.low_stock_threshold,
        Product.is_active == True
    ).limit(10).all()
    
    # Recent sales
    recent_sales = Sale.query.filter_by(shop_id=shop_id).order_by(desc(Sale.created_at)).limit(10).all()
    
    # Cashier performance today
    cashier_performance = db.session.query(
        User.username,
        func.count(Sale.id).label('sale_count'),
        func.sum(Sale.total_amount).label('total_amount')
    ).join(Sale, User.id == Sale.cashier_id).filter(
        Sale.shop_id == shop_id,
        func.date(Sale.created_at) == today,
        Sale.status == 'completed'
    ).group_by(User.id, User.username).all()
    
    # Sales trend data for the past 7 days
    sales_trend = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        daily_sales = db.session.query(func.sum(Sale.total_amount)).filter(
            Sale.shop_id == shop_id,
            func.date(Sale.created_at) == date,
            Sale.status == 'completed'
        ).scalar() or 0
        sales_trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'sales': float(daily_sales)
        })
    
    return render_template('shop_admin/dashboard.html',
                         today_sales=today_sales,
                         monthly_sales=monthly_sales,
                         top_products=top_products,
                         low_stock_products=low_stock_products,
                         recent_sales=recent_sales,
                         cashier_performance=cashier_performance,
                         sales_trend=sales_trend)

@bp.route('/products')
@require_shop_access
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', 0, type=int)
    
    query = Product.query.filter_by(shop_id=session['shop_id'])
    
    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) |
            (Product.barcode.ilike(f'%{search}%')) |
            (Product.sku.ilike(f'%{search}%'))
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    products = query.order_by(Product.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = Category.query.filter_by(shop_id=session['shop_id']).all()
    
    return render_template('shop_admin/products.html', 
                         products=products, categories=categories, 
                         search=search, selected_category=category_id)

@bp.route('/products/add', methods=['GET', 'POST'])
@require_shop_access
def add_product():
    if request.method == 'POST':
        product = Product(
            name=request.form['name'],
            description=request.form.get('description', ''),
            price=float(request.form['price']),
            cost_price=float(request.form.get('cost_price', 0)),
            barcode=request.form.get('barcode', ''),
            sku=request.form.get('sku', ''),
            stock_quantity=int(request.form.get('stock_quantity', 0)),
            low_stock_threshold=int(request.form.get('low_stock_threshold', 10)),
            category_id=int(request.form['category_id']) if request.form['category_id'] else None,
            shop_id=session['shop_id']
        )
        
        db.session.add(product)
        db.session.flush()
        
        # Create stock movement if initial stock
        if product.stock_quantity > 0:
            movement = StockMovement(
                product_id=product.id,
                movement_type='in',
                quantity=product.stock_quantity,
                reference='initial_stock',
                notes='Initial stock entry',
                created_by=session['user_id']
            )
            db.session.add(movement)
        
        db.session.commit()
        
        log_audit(session['user_id'], 'add_product', 'product', product.id,
                  request.remote_addr, request.user_agent.string,
                  new_values={'name': product.name, 'price': float(product.price)})
        
        flash('Product added successfully', 'success')
        return redirect(url_for('shop_admin.products'))
    
    categories = Category.query.filter_by(shop_id=session['shop_id']).all()
    return render_template('shop_admin/add_product.html', categories=categories)

@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@require_shop_access
def edit_product(product_id):
    product = Product.query.filter_by(id=product_id, shop_id=session['shop_id']).first_or_404()
    
    if request.method == 'POST':
        old_values = {
            'name': product.name,
            'price': float(product.price),
            'stock_quantity': product.stock_quantity
        }
        
        product.name = request.form['name']
        product.description = request.form.get('description', '')
        product.price = float(request.form['price'])
        product.cost_price = float(request.form.get('cost_price', 0))
        product.barcode = request.form.get('barcode', '')
        product.sku = request.form.get('sku', '')
        
        # Handle stock quantity change
        new_stock = int(request.form.get('stock_quantity', 0))
        if new_stock != product.stock_quantity:
            movement_type = 'in' if new_stock > product.stock_quantity else 'out'
            quantity_change = abs(new_stock - product.stock_quantity)
            
            movement = StockMovement(
                product_id=product.id,
                movement_type=movement_type,
                quantity=quantity_change,
                reference='manual_adjustment',
                notes=f'Stock adjusted from {product.stock_quantity} to {new_stock}',
                created_by=session['user_id']
            )
            db.session.add(movement)
            product.stock_quantity = new_stock
        
        product.low_stock_threshold = int(request.form.get('low_stock_threshold', 10))
        product.category_id = int(request.form['category_id']) if request.form['category_id'] else None
        product.updated_at = datetime.now()
        
        db.session.commit()
        
        log_audit(session['user_id'], 'edit_product', 'product', product_id,
                  request.remote_addr, request.user_agent.string,
                  old_values=old_values,
                  new_values={
                      'name': product.name,
                      'price': float(product.price),
                      'stock_quantity': product.stock_quantity
                  })
        
        flash('Product updated successfully', 'success')
        return redirect(url_for('shop_admin.products'))
    
    categories = Category.query.filter_by(shop_id=session['shop_id']).all()
    return render_template('shop_admin/edit_product.html', product=product, categories=categories)

@bp.route('/products/<int:product_id>/delete', methods=['POST'])
@require_shop_access
def delete_product(product_id):
    product = Product.query.filter_by(id=product_id, shop_id=session['shop_id']).first_or_404()
    
    # Check if product has sales
    has_sales = Sale.query.join(SaleItem).filter(SaleItem.product_id == product_id).first()
    if has_sales:
        flash('Cannot delete product with existing sales. Mark as inactive instead.', 'error')
        return redirect(url_for('shop_admin.products'))
    
    db.session.delete(product)
    db.session.commit()
    
    log_audit(session['user_id'], 'delete_product', 'product', product_id,
              request.remote_addr, request.user_agent.string,
              old_values={'name': product.name})
    
    flash('Product deleted successfully', 'success')
    return redirect(url_for('shop_admin.products'))

@bp.route('/products/<int:product_id>/toggle', methods=['POST'])
@require_shop_access
def toggle_product_status(product_id):
    product = Product.query.filter_by(id=product_id, shop_id=session['shop_id']).first_or_404()
    
    old_status = product.is_active
    product.is_active = not product.is_active
    product.updated_at = datetime.now()
    
    db.session.commit()
    
    log_audit(session['user_id'], 'toggle_product_status', 'product', product_id,
              request.remote_addr, request.user_agent.string,
              old_values={'is_active': old_status},
              new_values={'is_active': product.is_active})
    
    status_text = 'activated' if product.is_active else 'deactivated'
    flash(f'Product {status_text} successfully', 'success')
    return redirect(url_for('shop_admin.products'))

@bp.route('/categories')
@require_shop_access
def categories():
    categories = Category.query.filter_by(shop_id=session['shop_id']).all()
    return render_template('shop_admin/categories.html', categories=categories)

@bp.route('/categories/add', methods=['POST'])
@require_shop_access
def add_category():
    name = request.form['name'].strip()
    
    if not name:
        flash('Category name is required', 'error')
        return redirect(url_for('shop_admin.categories'))
    
    # Check if category already exists for this shop
    existing = Category.query.filter_by(name=name, shop_id=session['shop_id']).first()
    if existing:
        flash('Category already exists', 'error')
        return redirect(url_for('shop_admin.categories'))
    
    category = Category(name=name, shop_id=session['shop_id'])
    db.session.add(category)
    db.session.commit()
    
    log_audit(session['user_id'], 'add_category', 'category', category.id,
              request.remote_addr, request.user_agent.string,
              new_values={'name': name})
    
    flash('Category added successfully', 'success')
    return redirect(url_for('shop_admin.categories'))

@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@require_shop_access
def edit_category(category_id):
    category = Category.query.filter_by(id=category_id, shop_id=session['shop_id']).first_or_404()
    
    if request.method == 'POST':
        new_name = request.form['name'].strip()
        
        if not new_name:
            flash('Category name is required', 'error')
            return render_template('shop_admin/edit_category.html', category=category)
        
        # Check if new name already exists
        existing = Category.query.filter_by(name=new_name, shop_id=session['shop_id']).filter(Category.id != category_id).first()
        if existing:
            flash('Category name already exists', 'error')
            return render_template('shop_admin/edit_category.html', category=category)
        
        old_name = category.name
        category.name = new_name
        db.session.commit()
        
        log_audit(session['user_id'], 'edit_category', 'category', category_id,
                  request.remote_addr, request.user_agent.string,
                  old_values={'name': old_name},
                  new_values={'name': new_name})
        
        flash('Category updated successfully', 'success')
        return redirect(url_for('shop_admin.categories'))
    
    return render_template('shop_admin/edit_category.html', category=category)

@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@require_shop_access
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id, shop_id=session['shop_id']).first_or_404()
    
    # Check if category has products
    has_products = Product.query.filter_by(category_id=category_id, shop_id=session['shop_id']).first()
    if has_products:
        flash('Cannot delete category with existing products. Move products to another category first.', 'error')
        return redirect(url_for('shop_admin.categories'))
    
    category_name = category.name
    db.session.delete(category)
    db.session.commit()
    
    log_audit(session['user_id'], 'delete_category', 'category', category_id,
              request.remote_addr, request.user_agent.string,
              old_values={'name': category_name})
    
    flash('Category deleted successfully', 'success')
    return redirect(url_for('shop_admin.categories'))

@bp.route('/sales')
@require_shop_access
def sales():
    page = request.args.get('page', 1, type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    cashier_id = request.args.get('cashier', 0, type=int)
    
    query = Sale.query.filter_by(shop_id=session['shop_id']).order_by(desc(Sale.created_at))
    
    if start_date:
        query = query.filter(Sale.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
    
    if end_date:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Sale.created_at < end_datetime)
    
    if cashier_id:
        query = query.filter_by(cashier_id=cashier_id)
    
    sales = query.paginate(page=page, per_page=20, error_out=False)
    
    # Get cashiers for filter
    cashiers = User.query.filter_by(shop_id=session['shop_id'], role='cashier', is_active=True).all()
    
    return render_template('shop_admin/sales.html', sales=sales, cashiers=cashiers,
                         start_date=start_date, end_date=end_date, selected_cashier=cashier_id)

@bp.route('/sales/<int:sale_id>/refund', methods=['POST'])
@require_shop_access
def refund_sale(sale_id):
    sale = Sale.query.filter_by(id=sale_id, shop_id=session['shop_id']).first_or_404()
    
    if sale.status != 'completed':
        flash('Can only refund completed sales', 'error')
        return redirect(url_for('shop_admin.sales'))
    
    reason = request.form['reason']
    
    # Restore stock quantities
    for item in sale.items:
        product = item.product
        product.stock_quantity += item.quantity
        
        # Create stock movement
        movement = StockMovement(
            product_id=product.id,
            movement_type='in',
            quantity=item.quantity,
            reference=f'refund_{sale.receipt_number}',
            notes=f'Refund: {reason}',
            created_by=session['user_id']
        )
        db.session.add(movement)
    
    sale.status = 'refunded'
    sale.refund_reason = reason
    db.session.commit()
    
    log_audit(session['user_id'], 'refund_sale', 'sale', sale_id,
              request.remote_addr, request.user_agent.string,
              new_values={'status': 'refunded', 'reason': reason})
    
    flash('Sale refunded successfully', 'success')
    return redirect(url_for('shop_admin.sales'))

@bp.route('/cashiers')
@require_shop_access
def cashiers():
    cashiers = User.query.filter_by(shop_id=session['shop_id'], role='cashier').all()
    return render_template('shop_admin/cashiers.html', cashiers=cashiers)

@bp.route('/cashiers/add', methods=['GET', 'POST'])
@require_shop_access
def add_cashier():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username/email exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('shop_admin/add_cashier.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('shop_admin/add_cashier.html')
        
        cashier = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='cashier',
            shop_id=session['shop_id'],
            user_active=True
        )
        
        db.session.add(cashier)
        db.session.commit()
        
        log_audit(session['user_id'], 'add_cashier', 'user', cashier.id,
                  request.remote_addr, request.user_agent.string,
                  new_values={'username': username, 'email': email})
        
        flash('Cashier added successfully', 'success')
        return redirect(url_for('shop_admin.cashiers'))
    
    return render_template('shop_admin/add_cashier.html')

@bp.route('/cashiers/<int:cashier_id>/edit', methods=['GET', 'POST'])
@require_shop_access
def edit_cashier(cashier_id):
    cashier = User.query.filter_by(id=cashier_id, shop_id=session['shop_id'], role='cashier').first_or_404()
    
    if request.method == 'POST':
        old_values = {
            'username': cashier.username,
            'email': cashier.email,
            'user_active': cashier.user_active
        }
        
        new_username = request.form['username']
        new_email = request.form['email']
        
        # Check if username/email exists (excluding current user)
        if User.query.filter_by(username=new_username).filter(User.id != cashier_id).first():
            flash('Username already exists', 'error')
            return render_template('shop_admin/edit_cashier.html', cashier=cashier)
        
        if User.query.filter_by(email=new_email).filter(User.id != cashier_id).first():
            flash('Email already exists', 'error')
            return render_template('shop_admin/edit_cashier.html', cashier=cashier)
        
        cashier.username = new_username
        cashier.email = new_email
        
        # Update password if provided
        new_password = request.form.get('password', '').strip()
        if new_password:
            cashier.password_hash = generate_password_hash(new_password)
        
        # Update active status
        cashier.user_active = 'user_active' in request.form
        
        db.session.commit()
        
        log_audit(session['user_id'], 'edit_cashier', 'user', cashier_id,
                  request.remote_addr, request.user_agent.string,
                  old_values=old_values,
                  new_values={
                      'username': cashier.username,
                      'email': cashier.email,
                      'user_active': cashier.user_active
                  })
        
        flash('Cashier updated successfully', 'success')
        return redirect(url_for('shop_admin.cashiers'))
    
    return render_template('shop_admin/edit_cashier.html', cashier=cashier)

@bp.route('/cashiers/<int:cashier_id>/toggle', methods=['POST'])
@require_shop_access
def toggle_cashier_status(cashier_id):
    cashier = User.query.filter_by(id=cashier_id, shop_id=session['shop_id'], role='cashier').first_or_404()
    
    old_status = cashier.user_active
    cashier.user_active = not cashier.user_active
    
    db.session.commit()
    
    log_audit(session['user_id'], 'toggle_cashier_status', 'user', cashier_id,
              request.remote_addr, request.user_agent.string,
              old_values={'user_active': old_status},
              new_values={'user_active': cashier.user_active})
    
    status_text = 'activated' if cashier.user_active else 'deactivated'
    flash(f'Cashier {status_text} successfully', 'success')
    return redirect(url_for('shop_admin.cashiers'))

@bp.route('/cashiers/<int:cashier_id>/delete', methods=['POST'])
@require_shop_access
def delete_cashier(cashier_id):
    cashier = User.query.filter_by(id=cashier_id, shop_id=session['shop_id'], role='cashier').first_or_404()
    
    # Check if cashier has sales
    has_sales = Sale.query.filter_by(cashier_id=cashier_id, shop_id=session['shop_id']).first()
    if has_sales:
        flash('Cannot delete cashier with existing sales. Deactivate instead.', 'error')
        return redirect(url_for('shop_admin.cashiers'))
    
    cashier_name = cashier.username
    db.session.delete(cashier)
    db.session.commit()
    
    log_audit(session['user_id'], 'delete_cashier', 'user', cashier_id,
              request.remote_addr, request.user_agent.string,
              old_values={'username': cashier_name})
    
    flash('Cashier deleted successfully', 'success')
    return redirect(url_for('shop_admin.cashiers'))

@bp.route('/settings', methods=['GET', 'POST'])
@require_shop_access
def settings():
    shop = Shop.query.get(session['shop_id'])
    
    if request.method == 'POST':
        old_values = {
            'name': shop.name,
            'owner_name': shop.owner_name,
            'email': shop.email,
            'phone': shop.phone
        }
        
        shop.name = request.form['name']
        shop.owner_name = request.form['owner_name']
        shop.email = request.form['email']
        shop.phone = request.form['phone']
        shop.address = request.form['address']
        
        # Update till number if provided
        if request.form.get('till_number'):
            shop.till_number = request.form['till_number']
        
        # Update shop settings
        settings = shop.settings or {}
        settings.update({
            'tax_rate': float(request.form.get('tax_rate', 16)),
            'receipt_header': request.form.get('receipt_header', ''),
            'receipt_footer': request.form.get('receipt_footer', 'Thank you for shopping with us!'),
            'enable_discounts': 'enable_discounts' in request.form,
            'mpesa_confirmation': 'mpesa_confirmation' in request.form,
            'auto_register_webhooks': 'auto_register_webhooks' in request.form,
            'theme': request.form.get('theme', 'light')
        })
        shop.settings = settings
        
        db.session.commit()
        
        log_audit(session['user_id'], 'update_shop_settings', 'shop', shop.id,
                  request.remote_addr, request.user_agent.string,
                  old_values=old_values,
                  new_values={
                      'name': shop.name,
                      'owner_name': shop.owner_name,
                      'email': shop.email,
                      'phone': shop.phone
                  })
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('shop_admin.settings'))
    
    return render_template('shop_admin/settings.html', shop=shop)

@bp.route('/reports')
@require_shop_access
def reports():
    return render_template('shop_admin/reports.html')

@bp.route('/reports/sales')
@require_shop_access
def sales_report():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    report_type = request.args.get('type', 'summary')
    
    # Default to current month if no dates provided
    if not start_date:
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    # Base query for sales in date range
    base_query = Sale.query.filter(
        Sale.shop_id == session['shop_id'],
        Sale.created_at >= start_datetime,
        Sale.created_at < end_datetime,
        Sale.status == 'completed'
    )
    
    # Summary data
    total_sales = base_query.count()
    total_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.shop_id == session['shop_id'],
        Sale.created_at >= start_datetime,
        Sale.created_at < end_datetime,
        Sale.status == 'completed'
    ).scalar() or 0
    
    # Payment method breakdown
    payment_breakdown = db.session.query(
        Sale.payment_method,
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_amount).label('total')
    ).filter(
        Sale.shop_id == session['shop_id'],
        Sale.created_at >= start_datetime,
        Sale.created_at < end_datetime,
        Sale.status == 'completed'
    ).group_by(Sale.payment_method).all()
    
    # Daily sales if detailed report
    daily_sales = []
    if report_type == 'detailed':
        daily_sales = db.session.query(
            func.date(Sale.created_at).label('date'),
            func.count(Sale.id).label('transaction_count'),
            func.sum(Sale.total_amount).label('total_amount')
        ).filter(
            Sale.shop_id == session['shop_id'],
            Sale.created_at >= start_datetime,
            Sale.created_at < end_datetime,
            Sale.status == 'completed'
        ).group_by(func.date(Sale.created_at)).order_by(func.date(Sale.created_at)).all()
    
    return render_template('shop_admin/sales_report.html',
                         start_date=start_date,
                         end_date=end_date,
                         report_type=report_type,
                         total_sales=total_sales,
                         total_revenue=total_revenue,
                         payment_breakdown=payment_breakdown,
                         daily_sales=daily_sales)

@bp.route('/reports/inventory')
@require_shop_access
def inventory_report():
    category_filter = request.args.get('category', '', type=int)
    status_filter = request.args.get('status', 'all')
    
    # Base query for products
    query = Product.query.filter_by(shop_id=session['shop_id'])
    
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    
    if status_filter == 'low_stock':
        query = query.filter(Product.stock_quantity <= Product.low_stock_threshold)
    elif status_filter == 'out_of_stock':
        query = query.filter(Product.stock_quantity <= 0)
    elif status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    products = query.order_by(Product.name).all()
    
    # Inventory summary
    total_products = Product.query.filter_by(shop_id=session['shop_id']).count()
    active_products = Product.query.filter_by(shop_id=session['shop_id'], is_active=True).count()
    low_stock_count = Product.query.filter(
        Product.shop_id == session['shop_id'],
        Product.stock_quantity <= Product.low_stock_threshold,
        Product.is_active == True
    ).count()
    out_of_stock_count = Product.query.filter(
        Product.shop_id == session['shop_id'],
        Product.stock_quantity <= 0,
        Product.is_active == True
    ).count()
    
    # Total inventory value
    inventory_value = db.session.query(
        func.sum(Product.cost_price * Product.stock_quantity)
    ).filter_by(shop_id=session['shop_id'], is_active=True).scalar() or 0
    
    categories = Category.query.filter_by(shop_id=session['shop_id']).all()
    
    return render_template('shop_admin/inventory_report.html',
                         products=products,
                         categories=categories,
                         selected_category=category_filter,
                         status_filter=status_filter,
                         total_products=total_products,
                         active_products=active_products,
                         low_stock_count=low_stock_count,
                         out_of_stock_count=out_of_stock_count,
                         inventory_value=inventory_value)

@bp.route('/reports/cashier-performance')
@require_shop_access
def cashier_performance_report():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Default to current month if no dates provided
    if not start_date:
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    # Cashier performance data
    cashier_stats = db.session.query(
        User.username,
        User.email,
        func.count(Sale.id).label('total_sales'),
        func.sum(Sale.total_amount).label('total_revenue'),
        func.avg(Sale.total_amount).label('avg_sale'),
        func.min(Sale.created_at).label('first_sale'),
        func.max(Sale.created_at).label('last_sale')
    ).join(Sale, User.id == Sale.cashier_id).filter(
        Sale.shop_id == session['shop_id'],
        Sale.created_at >= start_datetime,
        Sale.created_at < end_datetime,
        Sale.status == 'completed'
    ).group_by(User.id, User.username, User.email).order_by(func.sum(Sale.total_amount).desc()).all()
    
    return render_template('shop_admin/cashier_performance_report.html',
                         start_date=start_date,
                         end_date=end_date,
                         cashier_stats=cashier_stats)

@bp.route('/bulk-actions', methods=['POST'])
@require_shop_access
def bulk_actions():
    action = request.form.get('action')
    selected_items = request.form.getlist('selected_items')
    
    if not selected_items:
        flash('No items selected', 'error')
        return redirect(request.referrer or url_for('shop_admin.products'))
    
    if action == 'activate_products':
        Product.query.filter(
            Product.id.in_(selected_items),
            Product.shop_id == session['shop_id']
        ).update({'is_active': True}, synchronize_session=False)
        db.session.commit()
        flash(f'{len(selected_items)} products activated', 'success')
        
    elif action == 'deactivate_products':
        Product.query.filter(
            Product.id.in_(selected_items),
            Product.shop_id == session['shop_id']
        ).update({'is_active': False}, synchronize_session=False)
        db.session.commit()
        flash(f'{len(selected_items)} products deactivated', 'success')
        
    elif action == 'update_category':
        new_category_id = request.form.get('new_category_id')
        if new_category_id:
            Product.query.filter(
                Product.id.in_(selected_items),
                Product.shop_id == session['shop_id']
            ).update({'category_id': new_category_id}, synchronize_session=False)
            db.session.commit()
            flash(f'{len(selected_items)} products updated', 'success')
    
    return redirect(request.referrer or url_for('shop_admin.products'))
