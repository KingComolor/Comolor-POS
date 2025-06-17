# Desktop App Control System for Render Deployment
# Centralized management of desktop POS installations

from flask import Blueprint, request, jsonify, session
from models import Shop, User, SystemSettings, AuditLog
from app import db
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import logging
import os

bp = Blueprint('desktop_api', __name__, url_prefix='/api/desktop')

class DesktopManager:
    """Manages desktop app installations and control"""
    
    def __init__(self):
        self.api_version = "1.0.0"
        self.min_app_version = "1.0.0"
        self.secret_key = os.environ.get('DESKTOP_SECRET_KEY', 'comolor_desktop_2025')
        
    def generate_installation_key(self, shop_id, till_number):
        """Generate unique installation key for desktop app"""
        data = f"{shop_id}:{till_number}:{self.secret_key}"
        return hashlib.sha256(data.encode()).hexdigest()[:24]
    
    def verify_installation(self, shop_id, installation_key, app_version):
        """Verify desktop app installation is authorized"""
        shop = Shop.query.get(shop_id)
        
        if not shop:
            return False, "Shop not found"
            
        if not shop.is_active:
            return False, "Shop is inactive"
            
        if not shop.is_license_active():
            return False, "License expired - please renew"
            
        # Verify installation key
        expected_key = self.generate_installation_key(shop_id, shop.till_number or "")
        if installation_key != expected_key:
            return False, "Invalid installation key"
            
        # Check version compatibility
        if app_version < self.min_app_version:
            return False, f"App version {app_version} outdated. Minimum required: {self.min_app_version}"
            
        return True, "Authorized"
    
    def get_shop_config(self, shop_id):
        """Get configuration for desktop app"""
        shop = Shop.query.get(shop_id)
        if not shop:
            return None
            
        # Get Render app URL from environment or construct it
        base_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
        
        return {
            'shop_id': shop.id,
            'shop_name': shop.name,
            'till_number': shop.till_number,
            'owner_name': shop.owner_name,
            'settings': shop.settings or {},
            'server_config': {
                'base_url': base_url,
                'api_version': self.api_version,
                'heartbeat_interval': 60,  # seconds
                'sync_interval': 300,      # 5 minutes
                'offline_duration': 86400  # 24 hours max offline
            },
            'mpesa_config': {
                'till_number': shop.till_number,
                'environment': os.environ.get('MPESA_ENVIRONMENT', 'sandbox')
            }
        }

desktop_manager = DesktopManager()

@bp.route('/authenticate', methods=['POST'])
def authenticate_desktop():
    """Authenticate desktop app installation"""
    try:
        data = request.get_json()
        shop_id = data.get('shop_id')
        installation_key = data.get('installation_key')
        app_version = data.get('app_version', '0.0.0')
        machine_id = data.get('machine_id')
        
        if not all([shop_id, installation_key, machine_id]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required authentication data'
            }), 400
        
        # Verify installation
        is_valid, message = desktop_manager.verify_installation(
            shop_id, installation_key, app_version
        )
        
        if not is_valid:
            # Log failed authentication attempt
            AuditLog(
                shop_id=shop_id,
                action='desktop_auth_failed',
                entity_type='desktop_app',
                new_values={'reason': message, 'machine_id': machine_id},
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(AuditLog)
            db.session.commit()
            
            return jsonify({
                'status': 'unauthorized',
                'message': message,
                'action_required': 'license_renewal' if 'License' in message else 'update_app'
            }), 401
        
        # Get shop configuration
        config = desktop_manager.get_shop_config(shop_id)
        if not config:
            return jsonify({
                'status': 'error',
                'message': 'Failed to load shop configuration'
            }), 500
        
        # Generate session token
        session_token = generate_session_token(shop_id, machine_id)
        
        # Update shop's desktop info
        shop = Shop.query.get(shop_id)
        settings = shop.settings or {}
        settings.update({
            'desktop_last_auth': datetime.utcnow().isoformat(),
            'desktop_machine_id': machine_id,
            'desktop_app_version': app_version,
            'desktop_session_token': session_token
        })
        shop.settings = settings
        db.session.commit()
        
        # Log successful authentication
        logging.info(f"Desktop app authenticated: shop_id={shop_id}, machine_id={machine_id}")
        
        return jsonify({
            'status': 'authorized',
            'message': 'Authentication successful',
            'session_token': session_token,
            'config': config,
            'server_time': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Desktop authentication error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Authentication system error'
        }), 500

@bp.route('/heartbeat', methods=['POST'])
def desktop_heartbeat():
    """Receive heartbeat from desktop app"""
    try:
        data = request.get_json()
        shop_id = data.get('shop_id')
        session_token = data.get('session_token')
        machine_id = data.get('machine_id')
        app_status = data.get('status', {})
        
        # Verify session token
        if not verify_session_token(shop_id, session_token, machine_id):
            return jsonify({
                'status': 'unauthorized',
                'message': 'Invalid session token'
            }), 401
        
        # Update shop status
        shop = Shop.query.get(shop_id)
        if shop:
            settings = shop.settings or {}
            settings.update({
                'desktop_last_heartbeat': datetime.utcnow().isoformat(),
                'desktop_status': app_status,
                'desktop_online': True
            })
            shop.settings = settings
            db.session.commit()
        
        # Check for pending commands
        commands = get_pending_commands(shop_id)
        
        # Check license status
        license_status = 'active' if shop.is_license_active() else 'expired'
        
        return jsonify({
            'status': 'success',
            'server_time': datetime.utcnow().isoformat(),
            'license_status': license_status,
            'commands': commands,
            'force_sync': should_force_sync(shop_id)
        })
        
    except Exception as e:
        logging.error(f"Heartbeat error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Heartbeat failed'
        }), 500

@bp.route('/sync/<int:shop_id>', methods=['POST'])
def sync_desktop_data(shop_id):
    """Sync data between desktop app and server"""
    try:
        data = request.get_json()
        session_token = data.get('session_token')
        machine_id = data.get('machine_id')
        sync_data = data.get('sync_data', {})
        last_sync = data.get('last_sync')
        
        # Verify session
        if not verify_session_token(shop_id, session_token, machine_id):
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Process incoming data from desktop
        if sync_data:
            process_desktop_sync_data(shop_id, sync_data)
        
        # Get server changes since last sync
        server_changes = get_server_changes_since(shop_id, last_sync)
        
        return jsonify({
            'status': 'success',
            'changes': server_changes,
            'sync_timestamp': datetime.utcnow().isoformat(),
            'next_sync_interval': 300
        })
        
    except Exception as e:
        logging.error(f"Sync error for shop {shop_id}: {e}")
        return jsonify({'error': 'Sync failed'}), 500

@bp.route('/license-check/<int:shop_id>')
def check_desktop_license(shop_id):
    """Check license status for desktop app"""
    try:
        shop = Shop.query.get_or_404(shop_id)
        
        license_active = shop.is_license_active()
        days_remaining = 0
        
        if shop.license_expires:
            days_remaining = (shop.license_expires - datetime.utcnow()).days
            
        return jsonify({
            'shop_id': shop_id,
            'license_active': license_active,
            'license_expires': shop.license_expires.isoformat() if shop.license_expires else None,
            'days_remaining': max(0, days_remaining),
            'grace_period': days_remaining >= -7,  # 7-day grace period
            'renewal_required': days_remaining <= 7
        })
        
    except Exception as e:
        logging.error(f"License check error: {e}")
        return jsonify({'error': 'License check failed'}), 500

@bp.route('/remote-command', methods=['POST'])
def send_remote_command():
    """Send remote command to desktop app (super admin only)"""
    try:
        # Verify super admin access
        if not session.get('user_id') or session.get('role') != 'super_admin':
            return jsonify({'error': 'Unauthorized - Super admin required'}), 401
            
        data = request.get_json()
        shop_id = data.get('shop_id')
        command = data.get('command')
        params = data.get('params', {})
        
        # Store command for next heartbeat
        success = store_remote_command(shop_id, command, params)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Command "{command}" queued for shop {shop_id}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to queue command'
            }), 500
            
    except Exception as e:
        logging.error(f"Remote command error: {e}")
        return jsonify({'error': 'Command failed'}), 500

# Helper Functions

def generate_session_token(shop_id, machine_id):
    """Generate session token for desktop app"""
    secret = desktop_manager.secret_key
    timestamp = str(int(datetime.utcnow().timestamp()))
    data = f"{shop_id}:{machine_id}:{timestamp}"
    return hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()[:32]

def verify_session_token(shop_id, token, machine_id):
    """Verify desktop app session token"""
    shop = Shop.query.get(shop_id)
    if not shop:
        return False
        
    settings = shop.settings or {}
    stored_token = settings.get('desktop_session_token')
    stored_machine = settings.get('desktop_machine_id')
    
    return token == stored_token and machine_id == stored_machine

def get_pending_commands(shop_id):
    """Get pending remote commands for shop"""
    # In production, this would check a commands table
    # For now, return empty list
    return []

def should_force_sync(shop_id):
    """Check if desktop app should force immediate sync"""
    # Check if there are critical updates requiring immediate sync
    return False

def process_desktop_sync_data(shop_id, sync_data):
    """Process data sent from desktop app"""
    try:
        # Handle offline sales data
        if 'offline_sales' in sync_data:
            for sale_data in sync_data['offline_sales']:
                # Process offline sales that were made when disconnected
                pass
                
        # Handle inventory updates
        if 'inventory_updates' in sync_data:
            for update in sync_data['inventory_updates']:
                # Process inventory changes made offline
                pass
                
    except Exception as e:
        logging.error(f"Error processing desktop sync data: {e}")

def get_server_changes_since(shop_id, last_sync):
    """Get changes made on server since last sync"""
    if not last_sync:
        last_sync = (datetime.utcnow() - timedelta(days=1)).isoformat()
    
    last_sync_dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
    
    changes = {
        'products': [],
        'categories': [],
        'settings': {},
        'users': []
    }
    
    # Get products modified since last sync
    from models import Product, Category
    updated_products = Product.query.filter(
        Product.shop_id == shop_id,
        Product.updated_at > last_sync_dt
    ).all()
    
    for product in updated_products:
        changes['products'].append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'stock_quantity': product.stock_quantity,
            'is_active': product.is_active,
            'action': 'update'
        })
    
    return changes

def store_remote_command(shop_id, command, params):
    """Store remote command for shop"""
    try:
        # In production, store in dedicated commands table
        # For now, store in shop settings
        shop = Shop.query.get(shop_id)
        if shop:
            settings = shop.settings or {}
            commands = settings.get('pending_commands', [])
            commands.append({
                'command': command,
                'params': params,
                'created_at': datetime.utcnow().isoformat(),
                'executed': False
            })
            settings['pending_commands'] = commands
            shop.settings = settings
            db.session.commit()
            return True
    except Exception as e:
        logging.error(f"Error storing remote command: {e}")
    
    return False