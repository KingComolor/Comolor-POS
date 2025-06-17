# System MPesa Configuration Guide

This guide covers how to configure MPesa credentials within the Comolor POS system for production deployment.

## Super Admin Configuration

### Step 1: Access Super Admin Panel
1. Login with super admin credentials
2. Navigate to Settings > System Configuration
3. Go to Payment Settings section

### Step 2: Configure Global MPesa Settings
Enter the following credentials obtained from Safaricom:

```
MPesa Environment: Production
Consumer Key: [Your production consumer key]
Consumer Secret: [Your production consumer secret]
Passkey: [Your production passkey]
Business Shortcode: [Your business till number]
Callback Base URL: https://yourdomain.com
```

### Step 3: Configure License Payment Settings
Set up license payment processing:

```
License Payment Till: [Super admin till number - 0797237383]
License Payment Phone: 254797237383
License Price per Month: 1500
License Grace Period: 7 days
Auto-activation: Enabled
```

### Step 4: Test Super Admin Configuration
1. Create test license payment
2. Use your phone to send small amount to till
3. Verify system receives callback
4. Check license activation works
5. Confirm audit logs are created

## Shop Owner Configuration

### For Each Shop Registration:

### Step 1: Shop Admin Access
1. Shop owner logs in as shop admin
2. Goes to Settings > Payment Configuration
3. Accesses MPesa Integration section

### Step 2: Enter Shop MPesa Credentials
Shop admin enters their own credentials:

```
MPesa Environment: Production
Consumer Key: [Shop's consumer key]
Consumer Secret: [Shop's consumer secret]
Passkey: [Shop's passkey]
Till Number: [Shop's unique till number]
Business Name: [As registered with Safaricom]
```

### Step 3: Configure Transaction Settings
Set up transaction preferences:

```
Payment Timeout: 90 seconds
Auto-confirm Payments: Yes
Receipt Footer Text: "Thank you for shopping with us!"
SMS Notifications: Enabled
Print Receipts: Enabled
```

### Step 4: Test Shop Configuration
1. Create test sale
2. Process MPesa payment
3. Verify payment confirmation
4. Check receipt generation
5. Confirm inventory updates

## Database Schema Updates

### Add MPesa Columns to Shops Table

```sql
-- MPesa configuration for each shop
ALTER TABLE shops ADD COLUMN mpesa_consumer_key TEXT;
ALTER TABLE shops ADD COLUMN mpesa_consumer_secret TEXT;
ALTER TABLE shops ADD COLUMN mpesa_passkey TEXT;
ALTER TABLE shops ADD COLUMN mpesa_business_shortcode VARCHAR(20);
ALTER TABLE shops ADD COLUMN mpesa_environment VARCHAR(20) DEFAULT 'sandbox';
ALTER TABLE shops ADD COLUMN mpesa_active BOOLEAN DEFAULT FALSE;
ALTER TABLE shops ADD COLUMN mpesa_configured_at TIMESTAMP;
ALTER TABLE shops ADD COLUMN mpesa_test_passed BOOLEAN DEFAULT FALSE;
```

### Add System Settings for Super Admin

```sql
-- Global MPesa settings
INSERT INTO system_settings (key, value, description) VALUES
('mpesa_super_admin_consumer_key', '', 'Super admin MPesa consumer key'),
('mpesa_super_admin_consumer_secret', '', 'Super admin MPesa consumer secret'),
('mpesa_super_admin_passkey', '', 'Super admin MPesa passkey'),
('mpesa_super_admin_shortcode', '123456', 'Super admin till number'),
('mpesa_license_phone', '254797237383', 'Phone for license payments'),
('mpesa_license_price', '1500', 'Monthly license price in KSh'),
('mpesa_environment', 'production', 'MPesa environment'),
('mpesa_callback_base_url', 'https://yourdomain.com', 'Base URL for callbacks');
```

## Implementation in Code

### Update Shop Model

```python
# In models.py - Add to Shop class
class Shop(db.Model):
    # ... existing fields ...
    
    # MPesa Configuration
    mpesa_consumer_key = db.Column(db.Text)
    mpesa_consumer_secret = db.Column(db.Text)
    mpesa_passkey = db.Column(db.Text)
    mpesa_business_shortcode = db.Column(db.String(20))
    mpesa_environment = db.Column(db.String(20), default='sandbox')
    mpesa_active = db.Column(db.Boolean, default=False)
    mpesa_configured_at = db.Column(db.DateTime)
    mpesa_test_passed = db.Column(db.Boolean, default=False)
    
    def has_mpesa_configured(self):
        return all([
            self.mpesa_consumer_key,
            self.mpesa_consumer_secret,
            self.mpesa_passkey,
            self.mpesa_business_shortcode
        ])
    
    def is_mpesa_active(self):
        return self.mpesa_active and self.has_mpesa_configured()
```

### Add Configuration Routes

```python
# In routes/shop_admin.py
@bp.route('/settings/mpesa', methods=['GET', 'POST'])
@login_required
def mpesa_settings():
    if current_user.role != 'shop_admin':
        abort(403)
    
    shop = current_user.shop
    if request.method == 'POST':
        # Update MPesa configuration
        shop.mpesa_consumer_key = request.form.get('consumer_key')
        shop.mpesa_consumer_secret = request.form.get('consumer_secret')
        shop.mpesa_passkey = request.form.get('passkey')
        shop.mpesa_business_shortcode = request.form.get('shortcode')
        shop.mpesa_environment = 'production'
        shop.mpesa_configured_at = datetime.utcnow()
        
        db.session.commit()
        flash('MPesa configuration updated successfully', 'success')
        
        # Test the configuration
        if test_mpesa_connection(shop):
            shop.mpesa_test_passed = True
            shop.mpesa_active = True
            db.session.commit()
            flash('MPesa connection test passed', 'success')
        else:
            flash('MPesa connection test failed', 'error')
    
    return render_template('shop_admin/mpesa_settings.html', shop=shop)
```

### Add Super Admin Configuration

```python
# In routes/super_admin.py
@bp.route('/settings/mpesa', methods=['GET', 'POST'])
@login_required
def system_mpesa_settings():
    if current_user.role != 'super_admin':
        abort(403)
    
    if request.method == 'POST':
        # Update system MPesa settings
        settings = {
            'mpesa_super_admin_consumer_key': request.form.get('consumer_key'),
            'mpesa_super_admin_consumer_secret': request.form.get('consumer_secret'),
            'mpesa_super_admin_passkey': request.form.get('passkey'),
            'mpesa_super_admin_shortcode': request.form.get('shortcode'),
            'mpesa_environment': 'production'
        }
        
        for key, value in settings.items():
            setting = SystemSettings.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = SystemSettings(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
        flash('System MPesa configuration updated', 'success')
    
    return render_template('super_admin/mpesa_settings.html')
```

## Security Implementation

### Encrypt Sensitive Data

```python
from cryptography.fernet import Fernet
import os

class MPesaEncryption:
    def __init__(self):
        self.key = os.environ.get('MPESA_ENCRYPTION_KEY')
        if not self.key:
            self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
    
    def encrypt(self, data):
        if not data:
            return None
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data):
        if not encrypted_data:
            return None
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()

# Usage in models
def set_mpesa_consumer_key(self, key):
    encryptor = MPesaEncryption()
    self.mpesa_consumer_key = encryptor.encrypt(key)

def get_mpesa_consumer_key(self):
    if not self.mpesa_consumer_key:
        return None
    encryptor = MPesaEncryption()
    return encryptor.decrypt(self.mpesa_consumer_key)
```

## Configuration Templates

### Shop MPesa Settings Template

```html
<!-- templates/shop_admin/mpesa_settings.html -->
<div class="card">
    <div class="card-header">
        <h5>MPesa Configuration</h5>
    </div>
    <div class="card-body">
        <form method="POST">
            <div class="mb-3">
                <label class="form-label">Consumer Key</label>
                <input type="password" class="form-control" name="consumer_key" required>
                <small class="text-muted">From Safaricom Developer Portal</small>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Consumer Secret</label>
                <input type="password" class="form-control" name="consumer_secret" required>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Passkey</label>
                <input type="password" class="form-control" name="passkey" required>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Till Number</label>
                <input type="text" class="form-control" name="shortcode" required>
                <small class="text-muted">Your M-Pesa for Business till number</small>
            </div>
            
            <button type="submit" class="btn btn-primary">Save & Test Configuration</button>
        </form>
    </div>
</div>
```

## Testing Procedures

### Super Admin Testing
1. Configure system credentials
2. Create test license payment
3. Send payment to super admin till
4. Verify automatic license activation
5. Check audit logs and notifications

### Shop Testing
1. Configure shop credentials
2. Create test sale
3. Process MPesa payment
4. Verify payment confirmation
5. Check receipt generation
6. Confirm inventory updates

## Monitoring and Maintenance

### Dashboard Metrics
- Track MPesa transaction success rates
- Monitor configuration status per shop
- Alert on failed transactions
- Report on license payment processing

### Regular Maintenance
1. Monthly credential rotation
2. Transaction log cleanup
3. Performance monitoring
4. Security audit of configurations
5. Backup of encrypted credentials

## Support Documentation

### For Shop Owners
- Step-by-step configuration guide
- Common error solutions
- Contact information for support
- Video tutorials for setup process

### For Technical Support
- Troubleshooting checklist
- Error code reference
- Log analysis procedures
- Escalation procedures for Safaricom issues

This configuration enables secure, scalable MPesa integration for both super admin license management and individual shop transaction processing.