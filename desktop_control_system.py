# Desktop App Control System for Comolor POS
# Allows centralized management of distributed desktop installations

from flask import Blueprint, request, jsonify
from models import Shop, User, SystemSettings
from app import db
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import logging

bp = Blueprint('desktop_control', __name__, url_prefix='/api/desktop')

class DesktopControlAPI:
    """Centralized control system for desktop app installations"""
    
    def __init__(self):
        self.api_version = "1.0"
        self.required_app_version = "1.0.0"
        
    def verify_installation(self, shop_id, installation_key, app_version):
        """Verify desktop app installation is authorized"""
        shop = Shop.query.get(shop_id)
        
        if not shop or not shop.is_active:
            return False, "Shop not active"
            
        if not shop.is_license_active():
            return False, "License expired"
            
        # Verify installation key
        expected_key = self.generate_installation_key(shop_id, shop.till_number)
        if installation_key != expected_key:
            return False, "Invalid installation key"
            
        # Check app version
        if not self.is_version_compatible(app_version):
            return False, f"App version {app_version} not supported. Please update to {self.required_app_version}"
            
        return True, "Authorized"
    
    def generate_installation_key(self, shop_id, till_number):
        """Generate unique installation key for a shop"""
        secret = "comolor_pos_desktop_secret_2025"
        data = f"{shop_id}:{till_number}:{secret}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def is_version_compatible(self, app_version):
        """Check if app version is compatible"""
        return app_version >= self.required_app_version
    
    def get_shop_configuration(self, shop_id):
        """Get shop-specific configuration for desktop app"""
        shop = Shop.query.get(shop_id)
        if not shop:
            return None
            
        return {
            'shop_id': shop.id,
            'shop_name': shop.name,
            'till_number': shop.till_number,
            'settings': shop.settings or {},
            'api_endpoints': {
                'sync_url': f"/api/desktop/sync/{shop_id}",
                'heartbeat_url': f"/api/desktop/heartbeat/{shop_id}",
                'update_check_url': f"/api/desktop/update-check/{shop_id}"
            },
            'sync_interval': 300,  # 5 minutes
            'heartbeat_interval': 60,  # 1 minute
            'offline_mode_duration': 86400  # 24 hours max offline
        }

desktop_control = DesktopControlAPI()

@bp.route('/auth/<int:shop_id>', methods=['POST'])
def authenticate_desktop_app(shop_id):
    """Authenticate desktop app installation"""
    try:
        data = request.get_json()
        installation_key = data.get('installation_key')
        app_version = data.get('app_version')
        machine_id = data.get('machine_id')
        
        is_valid, message = desktop_control.verify_installation(
            shop_id, installation_key, app_version
        )
        
        if not is_valid:
            return jsonify({
                'status': 'unauthorized',
                'message': message,
                'action_required': 'contact_admin' if 'License' in message else 'update_app'
            }), 401
        
        # Log successful authentication
        logging.info(f"Desktop app authenticated for shop {shop_id}, machine {machine_id}")
        
        # Get shop configuration
        config = desktop_control.get_shop_configuration(shop_id)
        
        return jsonify({
            'status': 'authorized',
            'message': 'Authentication successful',
            'config': config,
            'server_time': datetime.utcnow().isoformat(),
            'session_token': generate_session_token(shop_id, machine_id)
        })
        
    except Exception as e:
        logging.error(f"Desktop authentication error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@bp.route('/heartbeat/<int:shop_id>', methods=['POST'])
def desktop_heartbeat(shop_id):
    """Receive heartbeat from desktop app"""
    try:
        data = request.get_json()
        machine_id = data.get('machine_id')
        app_version = data.get('app_version')
        status = data.get('status', {})
        
        # Update shop's last seen timestamp
        shop = Shop.query.get(shop_id)
        if shop:
            settings = shop.settings or {}
            settings['desktop_last_seen'] = datetime.utcnow().isoformat()
            settings['desktop_machine_id'] = machine_id
            settings['desktop_app_version'] = app_version
            settings['desktop_status'] = status
            shop.settings = settings
            db.session.commit()
        
        # Check for remote commands
        commands = get_pending_commands(shop_id)
        
        return jsonify({
            'status': 'success',
            'server_time': datetime.utcnow().isoformat(),
            'commands': commands,
            'config_version': get_config_version(shop_id)
        })
        
    except Exception as e:
        logging.error(f"Heartbeat error for shop {shop_id}: {e}")
        return jsonify({'error': 'Heartbeat failed'}), 500

@bp.route('/sync/<int:shop_id>', methods=['POST'])
def sync_data(shop_id):
    """Sync data between desktop app and server"""
    try:
        data = request.get_json()
        sync_data = data.get('data', {})
        last_sync = data.get('last_sync')
        
        # Get changes since last sync
        changes = get_changes_since(shop_id, last_sync)
        
        # Process incoming changes from desktop
        if sync_data:
            process_desktop_changes(shop_id, sync_data)
        
        return jsonify({
            'status': 'success',
            'changes': changes,
            'sync_timestamp': datetime.utcnow().isoformat(),
            'next_sync_interval': 300
        })
        
    except Exception as e:
        logging.error(f"Sync error for shop {shop_id}: {e}")
        return jsonify({'error': 'Sync failed'}), 500

@bp.route('/update-check/<int:shop_id>')
def check_for_updates(shop_id):
    """Check if desktop app needs updates"""
    try:
        app_version = request.args.get('version', '0.0.0')
        
        update_available = app_version < desktop_control.required_app_version
        
        response = {
            'update_available': update_available,
            'current_version': app_version,
            'latest_version': desktop_control.required_app_version,
            'force_update': update_available and is_critical_update(app_version),
            'download_url': 'https://your-domain.com/downloads/comolor-pos-desktop-latest.exe',
            'release_notes': get_release_notes(desktop_control.required_app_version)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Update check error: {e}")
        return jsonify({'error': 'Update check failed'}), 500

@bp.route('/remote-command/<int:shop_id>', methods=['POST'])
def send_remote_command(shop_id):
    """Send remote command to desktop app"""
    try:
        # Only super admin can send commands
        if request.headers.get('Admin-Token') != get_admin_token():
            return jsonify({'error': 'Unauthorized'}), 401
            
        data = request.get_json()
        command = data.get('command')
        params = data.get('params', {})
        
        # Store command for next heartbeat
        store_command(shop_id, command, params)
        
        return jsonify({
            'status': 'success',
            'message': f'Command {command} queued for shop {shop_id}'
        })
        
    except Exception as e:
        logging.error(f"Remote command error: {e}")
        return jsonify({'error': 'Command failed'}), 500

@bp.route('/installation-key/<int:shop_id>')
def get_installation_key(shop_id):
    """Get installation key for desktop app setup"""
    try:
        # Only super admin can get installation keys
        if request.headers.get('Admin-Token') != get_admin_token():
            return jsonify({'error': 'Unauthorized'}), 401
            
        shop = Shop.query.get_or_404(shop_id)
        installation_key = desktop_control.generate_installation_key(
            shop_id, shop.till_number
        )
        
        return jsonify({
            'shop_id': shop_id,
            'shop_name': shop.name,
            'installation_key': installation_key,
            'download_url': 'https://your-domain.com/downloads/comolor-pos-desktop-setup.exe',
            'setup_instructions': get_setup_instructions()
        })
        
    except Exception as e:
        logging.error(f"Installation key error: {e}")
        return jsonify({'error': 'Failed to generate key'}), 500

# Helper functions
def generate_session_token(shop_id, machine_id):
    """Generate session token for desktop app"""
    secret = "session_secret_2025"
    data = f"{shop_id}:{machine_id}:{datetime.utcnow().isoformat()}"
    return hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()[:32]

def get_pending_commands(shop_id):
    """Get pending remote commands for shop"""
    # In production, this would fetch from a commands table
    return []

def get_config_version(shop_id):
    """Get current configuration version"""
    return int(datetime.utcnow().timestamp())

def get_changes_since(shop_id, last_sync):
    """Get data changes since last sync"""
    if not last_sync:
        last_sync = (datetime.utcnow() - timedelta(days=1)).isoformat()
    
    # Return recent changes for this shop
    return {
        'products': [],  # Modified products since last_sync
        'categories': [],  # Modified categories
        'settings': {}  # Updated settings
    }

def process_desktop_changes(shop_id, sync_data):
    """Process changes sent from desktop app"""
    # Handle offline sales, inventory updates, etc.
    pass

def is_critical_update(current_version):
    """Check if update is critical/mandatory"""
    critical_versions = ['1.0.0']  # Versions that require immediate update
    return current_version in critical_versions

def get_release_notes(version):
    """Get release notes for version"""
    return f"Comolor POS Desktop v{version} - Bug fixes and performance improvements"

def store_command(shop_id, command, params):
    """Store remote command for shop"""
    # In production, store in database table
    pass

def get_admin_token():
    """Get admin authorization token"""
    return "your_super_secret_admin_token_2025"

def get_setup_instructions():
    """Get desktop app setup instructions"""
    return {
        'steps': [
            'Download the installer from the provided URL',
            'Run installer as administrator',
            'Enter your shop ID and installation key',
            'Configure till number and printer settings',
            'Test connection to server',
            'Start using the POS system'
        ],
        'requirements': [
            'Windows 10 or later',
            'Internet connection for initial setup',
            'Thermal printer (optional)',
            'Barcode scanner (optional)'
        ]
    }