# Developer Guide - Comolor POS System

## Architecture Overview

The Comolor POS system is built with Flask (Python) backend and vanilla JavaScript frontend, designed for multi-tenant retail operations in Kenya.

### Technology Stack
- **Backend**: Flask 3.1.1, SQLAlchemy 2.0.41, PostgreSQL
- **Frontend**: Bootstrap 5.3.0, Vanilla JavaScript, Feather Icons
- **Authentication**: Flask-Login with session management
- **Payment Integration**: MPesa Daraja API
- **Deployment**: Gunicorn WSGI server

## Project Structure

```
├── app.py              # Flask application factory
├── main.py             # Application entry point
├── models.py           # Database models
├── routes/             # Route blueprints
│   ├── auth.py         # Authentication routes
│   ├── cashier.py      # POS/Cashier interface
│   ├── shop_admin.py   # Shop management
│   ├── super_admin.py  # System administration
│   └── mpesa.py        # Payment callbacks
├── utils/              # Utility modules
│   ├── auth.py         # Authentication helpers
│   ├── mpesa.py        # MPesa API integration
│   └── reports.py      # Report generation
├── static/             # Frontend assets
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript modules
│   └── images/         # Static images
├── templates/          # Jinja2 templates
└── docs/               # Documentation
```

## Database Design

### Multi-Tenant Architecture
The system uses a single database with tenant isolation via `shop_id` foreign keys:

```python
# Example model with tenant isolation
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    
    # Always query with shop_id filter
    @classmethod
    def get_by_shop(cls, shop_id):
        return cls.query.filter_by(shop_id=shop_id).all()
```

### Key Models

#### User Management
```python
class User(db.Model, UserMixin):
    # Multi-role system: super_admin, shop_admin, cashier
    role = db.Column(db.String(20), nullable=False, default='cashier')
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=True)
```

#### Shop Management
```python
class Shop(db.Model):
    # Multi-tenant shop definition
    is_active = db.Column(db.Boolean, default=False)
    license_expires = db.Column(db.DateTime)
    
    def is_license_active(self):
        return self.is_active and self.license_expires > datetime.utcnow()
```

#### Transaction Processing
```python
class Sale(db.Model):
    # Complete transaction record
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # cash, mpesa
    status = db.Column(db.String(20), default='completed')
```

## Development Setup

### Local Environment
```bash
# Clone repository
git clone <repository-url>
cd comolor-pos

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/comolor_pos"
export SESSION_SECRET="your-secret-key"
export FLASK_ENV="development"
export FLASK_DEBUG=1

# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Run development server
python main.py
```

### Replit Environment
```bash
# Environment is pre-configured
# Database automatically created
# Dependencies pre-installed
# Run with workflow: "Start application"
```

## Authentication System

### Role-Based Access Control
```python
from utils.auth import require_role, require_shop_access

# Require specific role
@require_role('super_admin')
def admin_only_function():
    pass

# Require shop access (shop_admin or cashier with valid shop)
@require_shop_access
def shop_function():
    # Automatically filters by current_user.shop_id
    pass
```

### Session Management
```python
# Login process
from flask_login import login_user, current_user

def authenticate_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return True
    return False
```

## API Integration

### MPesa Integration
```python
# utils/mpesa.py
class MpesaAPI:
    def __init__(self):
        self.consumer_key = os.environ.get('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET')
        self.base_url = self.get_base_url()
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK Push payment"""
        # Implementation details in mpesa-guide.md
        pass
```

### Callback Handling
```python
# routes/mpesa.py
@mpesa_bp.route('/c2b/confirmation', methods=['POST'])
def c2b_confirmation():
    """Handle payment confirmations from MPesa"""
    data = request.get_json()
    
    # Process payment
    # Update transaction status
    # Trigger inventory updates
    
    return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})
```

## Frontend Architecture

### JavaScript Modules
```javascript
// static/js/main.js - Core functionality
class AppCore {
    init() {
        this.setupEventListeners();
        this.initializeComponents();
    }
    
    async makeRequest(url, options = {}) {
        // Centralized API request handling
        // Error handling and loading states
    }
}

// static/js/barcode.js - Barcode scanner integration
class BarcodeScanner {
    constructor() {
        this.buffer = '';
        this.timeout = null;
    }
    
    handleInput(event) {
        // Process barcode scanner input
        // Trigger product lookup
    }
}
```

### Real-time Updates
```javascript
// static/js/mpesa.js - Payment status polling
class MpesaIntegration {
    async startPaymentPolling(saleId) {
        this.pollingInterval = setInterval(async () => {
            const status = await this.checkPaymentStatus(saleId);
            if (status.completed) {
                this.handlePaymentSuccess(status);
                this.stopPolling();
            }
        }, 2000);
    }
}
```

## Security Implementation

### Input Validation
```python
from flask_wtf.csrf import CSRFProtect
from wtforms import validators

# CSRF protection
csrf = CSRFProtect(app)

# Form validation
class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
```

### Data Sanitization
```python
from markupsafe import escape

def sanitize_input(user_input):
    """Sanitize user input to prevent XSS"""
    return escape(user_input)
```

### Audit Logging
```python
from utils.auth import log_audit

def create_product(product_data):
    # Create product
    product = Product(**product_data)
    db.session.add(product)
    db.session.commit()
    
    # Log action
    log_audit(
        user_id=current_user.id,
        action='create_product',
        entity_type='Product',
        entity_id=product.id,
        new_values=product_data
    )
```

## Testing

### Unit Testing
```python
import unittest
from app import app, db

class TestModels(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_user_creation(self):
        user = User(username='test', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        self.assertIsNotNone(user.id)
```

### Integration Testing
```python
class TestAPI(unittest.TestCase):
    def test_product_creation_endpoint(self):
        with self.app.test_client() as client:
            response = client.post('/shop-admin/add-product', data={
                'name': 'Test Product',
                'price': '100.00'
            })
            self.assertEqual(response.status_code, 302)
```

### Frontend Testing
```javascript
// Test barcode scanner functionality
function testBarcodeScanner() {
    const scanner = new BarcodeScanner();
    const testBarcode = '1234567890123';
    
    // Simulate barcode input
    scanner.processScan(testBarcode);
    
    // Verify product lookup triggered
    assert(scanner.lastScannedCode === testBarcode);
}
```

## Performance Optimization

### Database Optimization
```python
# Efficient queries with proper indexing
def get_shop_sales(shop_id, date_from, date_to):
    return Sale.query.filter(
        Sale.shop_id == shop_id,
        Sale.created_at.between(date_from, date_to)
    ).options(
        joinedload(Sale.items).joinedload(SaleItem.product)
    ).all()
```

### Caching Strategy
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_shop_categories(shop_id):
    """Cache shop categories for faster access"""
    return Category.query.filter_by(shop_id=shop_id).all()
```

### Frontend Optimization
```javascript
// Debounced search to reduce API calls
const debouncedSearch = debounce(function(query) {
    performProductSearch(query);
}, 300);

// Lazy loading for large product lists
function loadProductsLazily(container, products) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                loadNextBatch();
            }
        });
    });
}
```

## Error Handling

### Backend Error Handling
```python
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Custom exception handling
class ShopLicenseExpiredError(Exception):
    pass

def check_shop_license(shop_id):
    shop = Shop.query.get(shop_id)
    if not shop.is_license_active():
        raise ShopLicenseExpiredError("Shop license has expired")
```

### Frontend Error Handling
```javascript
class ErrorHandler {
    static async handleApiError(response) {
        if (!response.ok) {
            const error = await response.json();
            this.showUserFriendlyError(error);
            throw new Error(error.message);
        }
        return response;
    }
    
    static showUserFriendlyError(error) {
        const message = this.getErrorMessage(error.code);
        AppCore.showNotification(message, 'error');
    }
}
```

## Deployment

### Environment Configuration
```python
# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
```

### Gunicorn Configuration
```bash
# Start production server
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 main:app
```

### Database Migrations
```python
# Migration script example
from flask_migrate import Migrate

migrate = Migrate(app, db)

# Generate migration
# flask db migrate -m "Add new column"

# Apply migration
# flask db upgrade
```

## Monitoring and Logging

### Application Logging
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

logger = logging.getLogger(__name__)

# Log important events
logger.info(f"User {current_user.username} created sale {sale.id}")
logger.warning(f"Low stock alert for product {product.name}")
logger.error(f"MPesa payment failed: {error_message}")
```

### Performance Monitoring
```python
from time import time

def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time()
        result = func(*args, **kwargs)
        duration = time() - start_time
        
        if duration > 1.0:  # Log slow operations
            logger.warning(f"Slow operation: {func.__name__} took {duration:.2f}s")
        
        return result
    return wrapper
```

## Contributing Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Maintain consistent indentation (4 spaces)

### Git Workflow
```bash
# Feature development
git checkout -b feature/new-feature
git commit -m "feat: add new feature"
git push origin feature/new-feature

# Create pull request
# Code review and approval
# Merge to main branch
```

### Testing Requirements
- Write unit tests for all new functions
- Maintain test coverage above 80%
- Test all user roles and permissions
- Verify MPesa integration in sandbox

This developer guide provides the foundation for contributing to and extending the Comolor POS system.