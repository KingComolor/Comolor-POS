import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or os.urandom(32).hex()
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize Flask-Login
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Configure the database for production
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "postgresql://localhost/comolor_pos"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["WTF_CSRF_ENABLED"] = True
app.config["WTF_CSRF_TIME_LIMIT"] = None

# Initialize the app with the extension
db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    # Import models and routes
    import models  # noqa: F401
    from routes import auth, super_admin, shop_admin, cashier, mpesa
    
    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(super_admin.bp)
    app.register_blueprint(shop_admin.bp)
    app.register_blueprint(cashier.bp)
    app.register_blueprint(mpesa.bp)
    
    # Add root route
    @app.route('/')
    def index():
        from flask import redirect, url_for, session
        if 'user_id' in session:
            if session.get('role') == 'super_admin':
                return redirect(url_for('super_admin.dashboard'))
            elif session.get('role') == 'shop_admin':
                return redirect(url_for('shop_admin.dashboard'))
            else:
                return redirect(url_for('cashier.pos'))
        return redirect(url_for('homepage'))
    
    # Static pages routes
    @app.route('/home')
    def homepage():
        from flask import render_template
        return render_template('homepage.html')
    
    @app.route('/about')
    def about():
        from flask import render_template
        return render_template('about.html')
    
    @app.route('/privacy')
    def privacy():
        from flask import render_template
        return render_template('privacy.html')
    
    @app.route('/terms')
    def terms():
        from flask import render_template
        return render_template('terms.html')
    
    @app.route('/screenshots')
    def screenshots():
        from flask import render_template
        return render_template('screenshots.html')
    
    # Create all tables
    try:
        db.create_all()
        
        # Create default super admin if none exists
        from models import User, Shop, Product, Category
        from werkzeug.security import generate_password_hash
        from datetime import datetime, timedelta
        
        super_admin = User.query.filter_by(role='super_admin').first()
        if not super_admin:
            admin = User()
            admin.username = 'admin'
            admin.email = 'admin@comolor.com'
            admin.password_hash = generate_password_hash('admin123')
            admin.role = 'super_admin'
            admin.created_at = datetime.utcnow()
            db.session.add(admin)
            db.session.commit()
            logging.info("Created default super admin user: admin/admin123")
        
        # Create demo shop with sample data for testing
        demo_shop = Shop.query.filter_by(name='Demo Supermarket').first()
        if not demo_shop:
            # Create demo shop
            shop = Shop()
            shop.name = 'Demo Supermarket'
            shop.owner_name = 'John Doe'
            shop.email = 'demo@comolor.com'
            shop.phone = '+254712345678'
            shop.address = 'Nairobi CBD, Kenya'
            shop.till_number = 'TILL12345678'
            shop.is_active = True
            shop.license_expires = datetime.utcnow() + timedelta(days=365)
            shop.created_at = datetime.utcnow()
            db.session.add(shop)
            db.session.flush()
            
            # Create shop admin
            shop_admin = User()
            shop_admin.username = 'shopadmin'
            shop_admin.email = 'demo@comolor.com'
            shop_admin.password_hash = generate_password_hash('shop123')
            shop_admin.role = 'shop_admin'
            shop_admin.shop_id = shop.id
            shop_admin.user_active = True
            shop_admin.created_at = datetime.utcnow()
            db.session.add(shop_admin)
            
            # Create cashier
            cashier = User()
            cashier.username = 'cashier'
            cashier.email = 'cashier@comolor.com'
            cashier.password_hash = generate_password_hash('cash123')
            cashier.role = 'cashier'
            cashier.shop_id = shop.id
            cashier.user_active = True
            cashier.created_at = datetime.utcnow()
            db.session.add(cashier)
            
            # Create categories
            categories = [
                {'name': 'Groceries', 'shop_id': shop.id},
                {'name': 'Beverages', 'shop_id': shop.id},
                {'name': 'Household', 'shop_id': shop.id},
                {'name': 'Electronics', 'shop_id': shop.id}
            ]
            
            for cat_data in categories:
                category = Category(**cat_data)
                db.session.add(category)
            
            db.session.flush()
            
            # Get category IDs
            grocery_cat = Category.query.filter_by(name='Groceries', shop_id=shop.id).first()
            beverage_cat = Category.query.filter_by(name='Beverages', shop_id=shop.id).first()
            household_cat = Category.query.filter_by(name='Household', shop_id=shop.id).first()
            electronics_cat = Category.query.filter_by(name='Electronics', shop_id=shop.id).first()
            
            # Create sample products
            products = [
                {'name': 'Milk 1L', 'price': 60.00, 'cost_price': 45.00, 'stock_quantity': 50, 'category_id': grocery_cat.id, 'barcode': '1234567890123'},
                {'name': 'Bread White', 'price': 50.00, 'cost_price': 35.00, 'stock_quantity': 30, 'category_id': grocery_cat.id, 'barcode': '1234567890124'},
                {'name': 'Coca Cola 500ml', 'price': 80.00, 'cost_price': 60.00, 'stock_quantity': 100, 'category_id': beverage_cat.id, 'barcode': '1234567890125'},
                {'name': 'Water 500ml', 'price': 25.00, 'cost_price': 15.00, 'stock_quantity': 200, 'category_id': beverage_cat.id, 'barcode': '1234567890126'},
                {'name': 'Soap Bar', 'price': 45.00, 'cost_price': 30.00, 'stock_quantity': 75, 'category_id': household_cat.id, 'barcode': '1234567890127'},
                {'name': 'Toothpaste', 'price': 120.00, 'cost_price': 90.00, 'stock_quantity': 40, 'category_id': household_cat.id, 'barcode': '1234567890128'},
                {'name': 'Phone Charger', 'price': 500.00, 'cost_price': 350.00, 'stock_quantity': 25, 'category_id': electronics_cat.id, 'barcode': '1234567890129'},
                {'name': 'Earphones', 'price': 800.00, 'cost_price': 600.00, 'stock_quantity': 15, 'category_id': electronics_cat.id, 'barcode': '1234567890130'}
            ]
            
            for prod_data in products:
                product = Product()
                product.name = prod_data['name']
                product.price = prod_data['price']
                product.cost_price = prod_data['cost_price']
                product.stock_quantity = prod_data['stock_quantity']
                product.category_id = prod_data['category_id']
                product.barcode = prod_data['barcode']
                product.shop_id = shop.id
                product.is_active = True
                product.created_at = datetime.utcnow()
                db.session.add(product)
            
            db.session.commit()
            logging.info("Created demo shop with sample data - Login: shopadmin/shop123 or cashier/cash123")
    
    except Exception as e:
        logging.error(f"Database initialization error: {e}")

# Export the app for Vercel
def handler(request):
    return app(request.environ, lambda *args: None)

# For local development
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)