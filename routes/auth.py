from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, Shop, AuditLog
from app import db
from utils.auth import log_audit
import uuid

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.user_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html')
            
            # Check shop license if not super admin
            if user.role != 'super_admin' and user.shop:
                if not user.shop.is_active or not user.shop.is_license_active:
                    flash('Shop license has expired. Please renew your license.', 'error')
                    return render_template('auth/login.html')
            
            # Login successful
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['shop_id'] = user.shop_id
            
            # Update last login
            from datetime import datetime
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log audit
            log_audit(user.id, 'login', 'user', user.id, request.remote_addr, request.user_agent.string)
            
            # Redirect based on role
            if user.role == 'super_admin':
                return redirect(url_for('super_admin.dashboard'))
            elif user.role == 'shop_admin':
                return redirect(url_for('shop_admin.dashboard'))
            else:  # cashier
                return redirect(url_for('cashier.pos'))
                
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Shop details
        shop_name = request.form['shop_name']
        owner_name = request.form['owner_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        
        # Admin user details
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first() or Shop.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('auth/register.html')
        
        try:
            # Create shop
            shop = Shop()
            shop.name = shop_name
            shop.owner_name = owner_name
            shop.email = email
            shop.phone = phone
            shop.address = address
            shop.till_number = f"TILL{str(uuid.uuid4())[:8].upper()}"
            shop.is_active = False  # Needs activation after payment
            db.session.add(shop)
            db.session.flush()  # Get shop ID
            
            # Create shop admin user
            user = User()
            user.username = username
            user.email = email
            user.password_hash = generate_password_hash(password)
            user.role = 'shop_admin'
            user.shop_id = shop.id
            user.user_active = True
            db.session.add(user)
            db.session.commit()
            
            flash(f'Shop registered successfully! Your Till Number is: {shop.till_number}. Please pay KES 3,000 to activate your license.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html')

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            # In a real application, send email with reset link
            flash('Password reset instructions have been sent to your email.', 'info')
        else:
            flash('Email not found', 'error')
    
    return render_template('auth/forgot_password.html')

@bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_audit(user_id, 'logout', 'user', user_id, request.remote_addr, request.user_agent.string)
    
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        user = User.query.get(session['user_id'])
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('auth.login'))
        
        if not check_password_hash(user.password_hash, current_password):
            flash('Current password is incorrect', 'error')
        elif new_password != confirm_password:
            flash('New passwords do not match', 'error')
        else:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            log_audit(user.id, 'change_password', 'user', user.id, request.remote_addr, request.user_agent.string)
            flash('Password changed successfully', 'success')
            
            # Redirect based on role
            if user.role == 'super_admin':
                return redirect(url_for('super_admin.dashboard'))
            elif user.role == 'shop_admin':
                return redirect(url_for('shop_admin.dashboard'))
            else:
                return redirect(url_for('cashier.pos'))
    
    return render_template('auth/change_password.html')
