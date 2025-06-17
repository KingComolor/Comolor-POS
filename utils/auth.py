from functools import wraps
from flask import session, redirect, url_for, request
from models import AuditLog
from app import db
import logging

def require_role(required_role):
    """Decorator to require specific user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            
            user_role = session.get('role')
            if user_role != required_role:
                # Allow super_admin to access any role
                if user_role != 'super_admin':
                    return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_any_role(*roles):
    """Decorator to require any of the specified roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            
            user_role = session.get('role')
            if user_role not in roles:
                return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_audit(user_id, action, entity_type=None, entity_id=None, old_values=None, new_values=None, ip_address=None, user_agent=None, shop_id=None):
    """Log audit trail for important actions"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            shop_id=shop_id or session.get('shop_id'),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address or request.remote_addr,
            user_agent=user_agent or request.user_agent.string
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        logging.error(f"Failed to log audit: {e}")
        # Don't let audit logging failure break the main operation
        pass

def is_shop_active(shop_id):
    """Check if shop license is active"""
    from models import Shop
    from datetime import datetime
    
    shop = Shop.query.get(shop_id)
    if not shop:
        return False
    
    return shop.is_active and shop.license_expires > datetime.utcnow()

def require_shop_access(f):
    """Decorator to ensure user has access to their shop"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        # Super admin can access any shop
        if session.get('role') == 'super_admin':
            return f(*args, **kwargs)
        
        shop_id = session.get('shop_id')
        if not shop_id:
            return redirect(url_for('auth.login'))
        
        # Check if shop license is active
        if not is_shop_active(shop_id):
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged in user"""
    from models import User
    
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None