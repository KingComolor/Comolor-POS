# Database Deployment Guide

This guide walks you through deploying the multi-tenant PostgreSQL database to production servers step-by-step.

## Deployment Options

### Option 1: VPS/Cloud Server (Recommended)
- DigitalOcean, Linode, AWS EC2, Google Cloud
- Full control over database configuration
- Cost-effective for small to medium scale

### Option 2: Managed Database Services
- AWS RDS, Google Cloud SQL, DigitalOcean Managed Databases
- Automated backups and maintenance
- Higher cost but less management overhead

### Option 3: Render PostgreSQL (Simple)
- Easy deployment with Render
- Good for starting out
- Limited customization options

## Option 1: VPS Deployment (Step-by-Step)

### Step 1: Server Setup

```bash
# Connect to your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y postgresql postgresql-contrib nginx certbot python3-certbot-nginx ufw
```

### Step 2: PostgreSQL Installation and Configuration

```bash
# Start PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Secure PostgreSQL
sudo -u postgres psql
```

```sql
-- Create production database and user
CREATE DATABASE comolor_pos_production;
CREATE USER comolor_app WITH PASSWORD 'your_secure_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE comolor_pos_production TO comolor_app;
\c comolor_pos_production;
GRANT ALL ON SCHEMA public TO comolor_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO comolor_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO comolor_app;

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO comolor_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO comolor_app;

-- Exit
\q
```

### Step 3: Configure PostgreSQL for Production

Edit `/etc/postgresql/14/main/postgresql.conf`:

```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```

Add/modify these settings:

```conf
# Memory (adjust based on your server RAM)
shared_buffers = 256MB                    # 25% of RAM
effective_cache_size = 1GB                # 75% of RAM
work_mem = 4MB
maintenance_work_mem = 64MB

# Connections
max_connections = 100
listen_addresses = 'localhost'

# Performance
checkpoint_completion_target = 0.9
wal_buffers = 16MB
random_page_cost = 1.1                    # For SSD storage

# Logging (important for debugging)
log_destination = 'stderr'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_min_duration_statement = 1000         # Log slow queries
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d '
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Step 4: Create Database Schema

Create deployment script:

```bash
nano /home/deploy/setup_database.sql
```

```sql
-- Create all tables with proper indexes
\c comolor_pos_production;

-- Shops table (master tenant table)
CREATE TABLE IF NOT EXISTS shops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    owner_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    address TEXT,
    till_number VARCHAR(20) UNIQUE,
    license_expires TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings JSONB DEFAULT '{}'::jsonb
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'cashier',
    shop_id INTEGER REFERENCES shops(id),
    user_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    shop_id INTEGER NOT NULL REFERENCES shops(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    cost_price DECIMAL(10,2) DEFAULT 0,
    barcode VARCHAR(100) UNIQUE,
    sku VARCHAR(100),
    stock_quantity INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 10,
    shop_id INTEGER NOT NULL REFERENCES shops(id),
    category_id INTEGER REFERENCES categories(id),
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sales table
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    receipt_number VARCHAR(50) UNIQUE NOT NULL,
    shop_id INTEGER NOT NULL REFERENCES shops(id),
    cashier_id INTEGER NOT NULL REFERENCES users(id),
    subtotal DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    mpesa_receipt VARCHAR(100),
    customer_phone VARCHAR(15),
    customer_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'completed',
    refund_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sale items table
CREATE TABLE IF NOT EXISTS sale_items (
    id SERIAL PRIMARY KEY,
    sale_id INTEGER NOT NULL REFERENCES sales(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(10,2) NOT NULL
);

-- Stock movements table
CREATE TABLE IF NOT EXISTS stock_movements (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    movement_type VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    reference VARCHAR(100),
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MPesa transactions table
CREATE TABLE IF NOT EXISTS mpesa_transactions (
    id SERIAL PRIMARY KEY,
    transaction_type VARCHAR(20) NOT NULL,
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    bill_ref_number VARCHAR(100),
    amount DECIMAL(10,2) NOT NULL,
    msisdn VARCHAR(15) NOT NULL,
    first_name VARCHAR(100),
    middle_name VARCHAR(100),
    last_name VARCHAR(100),
    transaction_time TIMESTAMP NOT NULL,
    shop_id INTEGER REFERENCES shops(id),
    sale_id INTEGER REFERENCES sales(id),
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- License payments table
CREATE TABLE IF NOT EXISTS license_payments (
    id SERIAL PRIMARY KEY,
    shop_id INTEGER NOT NULL REFERENCES shops(id),
    amount DECIMAL(10,2) NOT NULL,
    mpesa_transaction_id VARCHAR(100) UNIQUE,
    payment_date TIMESTAMP NOT NULL,
    license_start TIMESTAMP NOT NULL,
    license_end TIMESTAMP NOT NULL,
    approved_by INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    shop_id INTEGER REFERENCES shops(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System settings table
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CRITICAL INDEXES FOR MULTI-TENANT PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_products_shop_id ON products(shop_id);
CREATE INDEX IF NOT EXISTS idx_sales_shop_id ON sales(shop_id);
CREATE INDEX IF NOT EXISTS idx_users_shop_id ON users(shop_id);
CREATE INDEX IF NOT EXISTS idx_categories_shop_id ON categories(shop_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id ON sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_product_id ON stock_movements(product_id);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_name_shop ON products(shop_id, name);
CREATE INDEX IF NOT EXISTS idx_sales_date_shop ON sales(shop_id, created_at);
CREATE INDEX IF NOT EXISTS idx_sales_receipt ON sales(receipt_number);
CREATE INDEX IF NOT EXISTS idx_products_active_shop ON products(shop_id, is_active);
CREATE INDEX IF NOT EXISTS idx_mpesa_transaction_id ON mpesa_transactions(transaction_id);

-- Insert default system settings
INSERT INTO system_settings (key, value, description) VALUES
    ('mpesa_environment', 'production', 'MPesa environment setting'),
    ('license_price_monthly', '1500', 'Monthly license price in KSh'),
    ('system_maintenance_mode', 'false', 'Enable maintenance mode'),
    ('max_shops_per_license', '1', 'Maximum shops per license')
ON CONFLICT (key) DO NOTHING;

-- Create default super admin (change password immediately!)
INSERT INTO users (username, email, password_hash, role) VALUES
    ('admin', 'admin@comolor.com', 'scrypt:32768:8:1$tXvE2KoZaFfEGJ2L$a4c5d5e6f7c8b9d0e1f2c3b4a5d6e7f8c9b0a1d2e3f4c5b6a7d8e9f0c1b2a3d4e5f6c7b8a9d0e1f2c3b4a5d6e7f8', 'super_admin')
ON CONFLICT (username) DO NOTHING;

COMMIT;
```

Run the setup:
```bash
sudo -u postgres psql -f /home/deploy/setup_database.sql
```

### Step 5: Application Deployment Environment

Create environment file:

```bash
nano /home/deploy/.env.production
```

```bash
# Database
DATABASE_URL=postgresql://comolor_app:your_secure_password@localhost/comolor_pos_production

# Security
SECRET_KEY=your_super_secure_secret_key_here
SESSION_SECRET=another_secure_session_key

# MPesa (add your production credentials)
MPESA_ENVIRONMENT=production
MPESA_CONSUMER_KEY=your_mpesa_consumer_key
MPESA_CONSUMER_SECRET=your_mpesa_consumer_secret
MPESA_PASSKEY=your_mpesa_passkey
MPESA_SHORTCODE=your_till_number

# System
FLASK_ENV=production
FLASK_DEBUG=False
MAX_CONTENT_LENGTH=16777216

# Logging
LOG_LEVEL=INFO
```

### Step 6: Firewall Configuration

```bash
# Configure UFW firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Check status
ufw status
```

### Step 7: SSL Certificate Setup

```bash
# Install SSL certificate (replace your-domain.com)
certbot --nginx -d your-domain.com

# Auto-renewal test
certbot renew --dry-run
```

## Option 2: Render Database Deployment

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub account
3. Connect your repository

### Step 2: Create PostgreSQL Database
1. Click "New +" → "PostgreSQL"
2. Configure:
   - Name: `comolor-pos-production`
   - Database: `comolor_pos`
   - User: `comolor_app`
   - Region: Choose closest to your users
   - Plan: Select based on needs

### Step 3: Get Connection Details
After creation, note:
- Host: `your-db-host.render.com`
- Database: `comolor_pos`
- Username: `comolor_app`
- Password: `generated_password`
- Port: `5432`

### Step 4: Connect and Setup Schema

```bash
# Connect using psql (install locally if needed)
psql "postgresql://comolor_app:password@your-host.render.com:5432/comolor_pos"
```

Run the same SQL setup script from Option 1.

## Database Migration and Seeding

### Migration Script

Create `migrate_to_production.py`:

```python
#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash

# Production database URL
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

def create_super_admin():
    """Create default super admin user"""
    with engine.connect() as conn:
        # Check if super admin exists
        result = conn.execute(text(
            "SELECT id FROM users WHERE role = 'super_admin' LIMIT 1"
        ))
        
        if result.fetchone():
            print("Super admin already exists")
            return
        
        # Create super admin
        password_hash = generate_password_hash('admin123')  # Change this!
        conn.execute(text("""
            INSERT INTO users (username, email, password_hash, role) 
            VALUES ('admin', 'admin@comolor.com', :password_hash, 'super_admin')
        """), {"password_hash": password_hash})
        
        conn.commit()
        print("Created super admin user: admin/admin123")
        print("WARNING: Change the default password immediately!")

def create_demo_shop():
    """Create a demo shop for testing"""
    with engine.connect() as conn:
        # Check if demo shop exists
        result = conn.execute(text(
            "SELECT id FROM shops WHERE email = 'demo@shop.com' LIMIT 1"
        ))
        
        if result.fetchone():
            print("Demo shop already exists")
            return
        
        # Create demo shop
        shop_result = conn.execute(text("""
            INSERT INTO shops (name, owner_name, email, phone, till_number, is_active) 
            VALUES ('Demo Electronics', 'John Doe', 'demo@shop.com', '0797237383', '123456', true)
            RETURNING id
        """))
        
        shop_id = shop_result.fetchone()[0]
        
        # Create shop admin
        password_hash = generate_password_hash('shop123')
        conn.execute(text("""
            INSERT INTO users (username, email, password_hash, role, shop_id) 
            VALUES ('shopadmin', 'admin@demo.com', :password_hash, 'shop_admin', :shop_id)
        """), {"password_hash": password_hash, "shop_id": shop_id})
        
        # Create cashier
        password_hash = generate_password_hash('cash123')
        conn.execute(text("""
            INSERT INTO users (username, email, password_hash, role, shop_id) 
            VALUES ('cashier', 'cashier@demo.com', :password_hash, 'cashier', :shop_id)
        """), {"password_hash": password_hash, "shop_id": shop_id})
        
        # Create category
        cat_result = conn.execute(text("""
            INSERT INTO categories (name, shop_id) 
            VALUES ('Electronics', :shop_id)
            RETURNING id
        """), {"shop_id": shop_id})
        
        category_id = cat_result.fetchone()[0]
        
        # Create sample products
        products = [
            ('Samsung Galaxy A54', 35000, 'Electronics smartphone', category_id),
            ('iPhone 15', 89000, 'Apple smartphone', category_id),
            ('Laptop Dell', 65000, 'Dell laptop computer', category_id)
        ]
        
        for name, price, desc, cat_id in products:
            conn.execute(text("""
                INSERT INTO products (name, price, description, shop_id, category_id, stock_quantity) 
                VALUES (:name, :price, :desc, :shop_id, :cat_id, 10)
            """), {
                "name": name, "price": price, "desc": desc, 
                "shop_id": shop_id, "cat_id": cat_id
            })
        
        conn.commit()
        print(f"Created demo shop (ID: {shop_id}) with sample data")
        print("Shop Admin: shopadmin/shop123")
        print("Cashier: cashier/cash123")

if __name__ == "__main__":
    try:
        create_super_admin()
        create_demo_shop()
        print("Database migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)
```

Run migration:
```bash
export DATABASE_URL="your_production_database_url"
python3 migrate_to_production.py
```

## Backup and Monitoring Setup

### Automated Backup Script

Create `/home/deploy/backup_database.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/postgresql"
DB_NAME="comolor_pos_production"
DB_USER="comolor_app"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
PGPASSWORD="your_password" pg_dump -h localhost -U $DB_USER $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/backup_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

Make executable and add to crontab:
```bash
chmod +x /home/deploy/backup_database.sh

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /home/deploy/backup_database.sh
```

### Database Monitoring

Create `/home/deploy/monitor_db.py`:

```python
#!/usr/bin/env python3
import psycopg2
import os
from datetime import datetime

def check_database_health():
    """Check database health and performance"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print(f"Database Health Check - {datetime.now()}")
    print("=" * 50)
    
    # Check connections
    cur.execute("SELECT count(*) FROM pg_stat_activity")
    connections = cur.fetchone()[0]
    print(f"Active connections: {connections}")
    
    # Check database size
    cur.execute("""
        SELECT pg_size_pretty(pg_database_size('comolor_pos_production'))
    """)
    db_size = cur.fetchone()[0]
    print(f"Database size: {db_size}")
    
    # Check shop count
    cur.execute("SELECT count(*) FROM shops WHERE is_active = true")
    active_shops = cur.fetchone()[0]
    print(f"Active shops: {active_shops}")
    
    # Check recent sales
    cur.execute("""
        SELECT count(*) FROM sales 
        WHERE created_at >= CURRENT_DATE
    """)
    today_sales = cur.fetchone()[0]
    print(f"Sales today: {today_sales}")
    
    # Check slow queries (if logging enabled)
    cur.execute("""
        SELECT query, calls, total_time, mean_time
        FROM pg_stat_statements
        WHERE mean_time > 1000
        ORDER BY mean_time DESC
        LIMIT 5
    """)
    
    slow_queries = cur.fetchall()
    if slow_queries:
        print("\nSlow queries (>1s):")
        for query, calls, total, mean in slow_queries:
            print(f"  Mean: {mean:.2f}ms, Calls: {calls}")
    
    conn.close()

if __name__ == "__main__":
    try:
        check_database_health()
    except Exception as e:
        print(f"Monitoring error: {e}")
```

## Security Checklist

- [ ] Database user has minimal required privileges
- [ ] PostgreSQL not accessible from internet
- [ ] Strong passwords for all database users
- [ ] SSL/TLS encryption enabled
- [ ] Regular security updates applied
- [ ] Firewall configured properly
- [ ] Backup files encrypted
- [ ] Audit logging enabled
- [ ] Connection pooling configured
- [ ] Row-level security considered for sensitive data

## Performance Tuning

### After Deployment

1. Monitor query performance
2. Analyze slow query logs
3. Add indexes for common queries
4. Adjust PostgreSQL memory settings
5. Set up read replicas if needed
6. Implement query caching
7. Consider partitioning for large tables

This deployment guide provides production-ready database setup with proper security, performance optimization, and monitoring for the Comolor POS multi-tenant system.