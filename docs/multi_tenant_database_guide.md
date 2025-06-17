# Multi-Tenant PostgreSQL Database Guide

This guide explains how to design, implement, and deploy a multi-tenant PostgreSQL database for the Comolor POS system.

## Understanding Multi-Tenancy

Multi-tenancy allows a single database to serve multiple customers (tenants) while keeping their data completely isolated. In Comolor POS, each shop is a tenant with their own products, sales, and users.

## Multi-Tenancy Patterns

### 1. Shared Database, Shared Schema (Current Approach)
- **One database, one schema, multiple shops**
- Each table has a `shop_id` column for data isolation
- Most cost-effective and easiest to maintain
- Used by Comolor POS

### 2. Shared Database, Separate Schemas
- One database with schema per tenant
- Better isolation but more complex
- Good for mid-size deployments

### 3. Separate Databases
- Complete database per tenant
- Maximum isolation but highest cost
- Enterprise-level deployments

## Comolor POS Database Design

### Core Multi-Tenant Structure

```sql
-- Master tenant table
CREATE TABLE shops (
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

-- Users belong to shops
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'cashier',
    shop_id INTEGER REFERENCES shops(id), -- TENANT ISOLATION
    user_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Products are shop-specific
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    shop_id INTEGER NOT NULL REFERENCES shops(id), -- TENANT ISOLATION
    category_id INTEGER REFERENCES categories(id),
    barcode VARCHAR(100) UNIQUE,
    stock_quantity INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sales are shop-specific
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    receipt_number VARCHAR(50) UNIQUE NOT NULL,
    shop_id INTEGER NOT NULL REFERENCES shops(id), -- TENANT ISOLATION
    cashier_id INTEGER NOT NULL REFERENCES users(id),
    total_amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tenant Isolation Rules

1. **Every tenant-specific table has shop_id**
2. **All queries include shop_id filter**
3. **Application enforces tenant boundaries**
4. **No cross-tenant data access**

## Production Database Setup

### 1. PostgreSQL Installation

#### Windows Installation

```powershell
# Download PostgreSQL installer from https://www.postgresql.org/download/windows/
# Or use Chocolatey package manager
choco install postgresql

# Or use winget
winget install PostgreSQL.PostgreSQL

# Start PostgreSQL service
net start postgresql-x64-14

# Connect to PostgreSQL
psql -U postgres
```

#### Alternative: Using Docker on Windows

```powershell
# Install Docker Desktop for Windows first
# Then run PostgreSQL container
docker run --name comolor-postgres `
  -e POSTGRES_PASSWORD=your_password `
  -e POSTGRES_DB=comolor_pos_production `
  -p 5432:5432 `
  -d postgres:14

# Connect to container
docker exec -it comolor-postgres psql -U postgres -d comolor_pos_production
```

#### Ubuntu/Debian Installation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check status
sudo systemctl status postgresql
```

### 2. Database Configuration

```bash
# Switch to postgres user
sudo -u postgres psql

-- Create production database
CREATE DATABASE comolor_pos_production;

-- Create application user
CREATE USER comolor_app WITH PASSWORD 'secure_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE comolor_pos_production TO comolor_app;

-- Connect to database
\c comolor_pos_production;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO comolor_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO comolor_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO comolor_app;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO comolor_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO comolor_app;
```

### 3. PostgreSQL Configuration Files

#### Windows Configuration

Configuration files are typically located in:
- `C:\Program Files\PostgreSQL\14\data\postgresql.conf`
- `C:\Program Files\PostgreSQL\14\data\pg_hba.conf`

Edit `postgresql.conf`:

```conf
# Memory settings (adjust based on server RAM)
shared_buffers = 256MB                  # 25% of RAM
effective_cache_size = 1GB              # 75% of RAM
work_mem = 4MB                          # Per connection work memory
maintenance_work_mem = 64MB             # Maintenance operations

# Connection settings
max_connections = 100                   # Adjust based on expected load
listen_addresses = 'localhost'          # '*' for remote connections
port = 5432

# Performance settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Logging (Windows paths)
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'all'                   # Log all SQL (disable in production)
log_duration = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

Edit `pg_hba.conf`:

```conf
# Database administrative login by Unix domain socket
local   all             postgres                                trust

# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5

# For remote connections (production):
host    comolor_pos_production  comolor_app     10.0.0.0/8      md5
```

Restart PostgreSQL on Windows:
```powershell
# Using Services
net stop postgresql-x64-14
net start postgresql-x64-14

# Or using Services GUI (services.msc)
# Find "postgresql-x64-14" service and restart
```

#### Linux Configuration

Edit `/etc/postgresql/14/main/postgresql.conf`:

```conf
# Memory settings (adjust based on server RAM)
shared_buffers = 256MB                  # 25% of RAM
effective_cache_size = 1GB              # 75% of RAM
work_mem = 4MB                          # Per connection work memory
maintenance_work_mem = 64MB             # Maintenance operations

# Connection settings
max_connections = 100                   # Adjust based on expected load
listen_addresses = 'localhost'          # '*' for remote connections

# Performance settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'all'                   # Log all SQL (disable in production)
log_duration = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

Edit `/etc/postgresql/14/main/pg_hba.conf`:

```conf
# Database administrative login by Unix domain socket
local   all             postgres                                peer

# "local" is for Unix domain socket connections only
local   all             all                                     peer

# IPv4 local connections:
host    all             all             127.0.0.1/32            md5

# IPv6 local connections:
host    all             all             ::1/128                 md5

# For remote connections (production):
host    comolor_pos_production  comolor_app     10.0.0.0/8      md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

## Application-Level Tenant Isolation

### 1. Database Connection with Tenant Context

```python
# In production_config.py
import os

class ProductionConfig:
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://comolor_app:secure_password@localhost/comolor_pos_production'
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,                    # Connection pool size
        'pool_recycle': 3600,               # Recycle connections every hour
        'pool_pre_ping': True,              # Verify connections before use
        'max_overflow': 30,                 # Extra connections if needed
        'pool_timeout': 30,                 # Timeout for getting connection
        'echo': False                       # Set to True for SQL debugging
    }
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### 2. Tenant-Aware Data Access Layer

```python
# In models.py - Tenant-aware base model
class TenantAwareModel(db.Model):
    __abstract__ = True
    
    @classmethod
    def query_for_shop(cls, shop_id):
        """Get query filtered by shop_id"""
        return cls.query.filter(cls.shop_id == shop_id)
    
    @classmethod
    def get_or_404_for_shop(cls, id, shop_id):
        """Get record by ID and shop_id or raise 404"""
        return cls.query.filter(
            cls.id == id, 
            cls.shop_id == shop_id
        ).first_or_404()

# Example usage in Product model
class Product(TenantAwareModel):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    
    # Tenant-aware methods
    @classmethod
    def get_active_products(cls, shop_id):
        return cls.query_for_shop(shop_id).filter(cls.is_active == True).all()
    
    @classmethod
    def search_products(cls, shop_id, search_term):
        return cls.query_for_shop(shop_id).filter(
            cls.name.ilike(f'%{search_term}%')
        ).all()
```

### 3. Route-Level Tenant Enforcement

```python
# In routes/shop_admin.py
from flask_login import current_user

def check_shop_access():
    """Ensure user can only access their shop's data"""
    if current_user.role == 'super_admin':
        return True  # Super admin can access all shops
    
    if not current_user.shop_id:
        abort(403, "User not assigned to any shop")
    
    return current_user.shop_id

@bp.route('/products')
@login_required
def products():
    shop_id = check_shop_access()
    if shop_id is True:  # Super admin
        products = Product.query.all()
    else:
        products = Product.query_for_shop(shop_id).all()
    
    return render_template('shop_admin/products.html', products=products)

@bp.route('/products/<int:product_id>')
@login_required
def edit_product(product_id):
    shop_id = check_shop_access()
    if shop_id is True:  # Super admin
        product = Product.query.get_or_404(product_id)
    else:
        product = Product.get_or_404_for_shop(product_id, shop_id)
    
    return render_template('shop_admin/edit_product.html', product=product)
```

## Database Performance Optimization

### 1. Essential Indexes

```sql
-- Tenant isolation indexes (CRITICAL)
CREATE INDEX idx_products_shop_id ON products(shop_id);
CREATE INDEX idx_sales_shop_id ON sales(shop_id);
CREATE INDEX idx_users_shop_id ON users(shop_id);
CREATE INDEX idx_categories_shop_id ON categories(shop_id);

-- Performance indexes
CREATE INDEX idx_products_barcode ON products(barcode);
CREATE INDEX idx_products_name_shop ON products(shop_id, name);
CREATE INDEX idx_sales_date_shop ON sales(shop_id, created_at);
CREATE INDEX idx_sales_receipt ON sales(receipt_number);

-- Composite indexes for common queries
CREATE INDEX idx_products_active_shop ON products(shop_id, is_active);
CREATE INDEX idx_sales_payment_method_shop ON sales(shop_id, payment_method);
```

### 2. Query Optimization

```sql
-- Example: Efficient tenant-filtered queries
EXPLAIN ANALYZE 
SELECT p.name, p.price, c.name as category 
FROM products p 
LEFT JOIN categories c ON p.category_id = c.id 
WHERE p.shop_id = 1 AND p.is_active = true
ORDER BY p.name;

-- Should use idx_products_active_shop index
```

### 3. Connection Pooling

```python
# In app.py - Production connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Production database connection with pooling
engine = create_engine(
    'postgresql://comolor_app:password@localhost/comolor_pos_production',
    poolclass=QueuePool,
    pool_size=20,           # Number of permanent connections
    max_overflow=30,        # Additional connections if needed
    pool_recycle=3600,      # Recycle connections every hour
    pool_pre_ping=True,     # Test connections before use
    pool_timeout=30,        # Timeout for getting connection
    echo=False              # Set True for debugging
)
```

## Security Best Practices

### 1. Network Security

```bash
# Firewall rules (UFW)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw deny 5432/tcp     # Block external PostgreSQL access
sudo ufw enable
```

### 2. Database Security

```sql
-- Create read-only user for reporting
CREATE USER comolor_readonly WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE comolor_pos_production TO comolor_readonly;
GRANT USAGE ON SCHEMA public TO comolor_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO comolor_readonly;

-- Row Level Security (Advanced)
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
CREATE POLICY products_tenant_policy ON products
    USING (shop_id = current_setting('app.current_shop_id')::INTEGER);
```

### 3. Application Security

```python
# Tenant context middleware
from flask import g, request, abort

@app.before_request
def set_tenant_context():
    """Set tenant context for each request"""
    if current_user.is_authenticated:
        if current_user.role == 'super_admin':
            g.shop_id = request.args.get('shop_id')  # Optional shop filter
        else:
            g.shop_id = current_user.shop_id
            if not g.shop_id:
                abort(403, "User not assigned to shop")
```

## Backup and Recovery

### 1. Automated Backups

#### Windows Backup Script

```powershell
# backup_script.ps1
$DATE = Get-Date -Format "yyyyMMdd_HHmmss"
$BACKUP_DIR = "C:\backup\postgresql"
$DB_NAME = "comolor_pos_production"
$PG_DUMP = "C:\Program Files\PostgreSQL\14\bin\pg_dump.exe"

# Create backup directory
New-Item -ItemType Directory -Force -Path $BACKUP_DIR

# Create backup
$env:PGPASSWORD = "your_password"
& $PG_DUMP -h localhost -U comolor_app $DB_NAME > "$BACKUP_DIR\backup_$DATE.sql"

# Compress backup
Compress-Archive -Path "$BACKUP_DIR\backup_$DATE.sql" -DestinationPath "$BACKUP_DIR\backup_$DATE.zip"
Remove-Item "$BACKUP_DIR\backup_$DATE.sql"

# Remove backups older than 30 days
Get-ChildItem -Path $BACKUP_DIR -Name "backup_*.zip" | 
Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } | 
Remove-Item -Force

# Upload to cloud storage (optional)
# aws s3 cp "$BACKUP_DIR\backup_$DATE.zip" s3://your-backup-bucket/
```

Schedule with Task Scheduler:
```powershell
# Create scheduled task for daily backup at 2 AM
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\scripts\backup_script.ps1"
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "PostgreSQL Backup" -Action $Action -Trigger $Trigger -Settings $Settings
```

#### Linux Backup Script

```bash
#!/bin/bash
# backup_script.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/postgresql"
DB_NAME="comolor_pos_production"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h localhost -U comolor_app -W $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/backup_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Upload to cloud storage (optional)
# aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://your-backup-bucket/
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/backup_script.sh
```

### 2. Point-in-Time Recovery

#### Windows WAL Archiving

```conf
# Enable WAL archiving in postgresql.conf (Windows)
wal_level = replica
archive_mode = on
archive_command = 'copy "%p" "C:\\backup\\postgresql\\wal_archive\\%f"'

# Create base backup
pg_basebackup -h localhost -D C:\backup\postgresql\base -U comolor_app -W -P -x
```

#### Linux WAL Archiving

```bash
# Enable WAL archiving in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/postgresql/wal_archive/%f'

# Create base backup
pg_basebackup -h localhost -D /backup/postgresql/base -U comolor_app -W -P -x
```

## Monitoring and Maintenance

### 1. Performance Monitoring

```sql
-- Check database size per tenant
SELECT 
    s.name as shop_name,
    COUNT(p.id) as product_count,
    COUNT(sa.id) as sales_count,
    pg_size_pretty(
        pg_total_relation_size('products') * COUNT(p.id) / 
        (SELECT COUNT(*) FROM products)
    ) as estimated_size
FROM shops s
LEFT JOIN products p ON s.id = p.shop_id
LEFT JOIN sales sa ON s.id = sa.shop_id
GROUP BY s.id, s.name
ORDER BY COUNT(sa.id) DESC;

-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### 2. Maintenance Tasks

```sql
-- Weekly maintenance (run during low usage)
VACUUM ANALYZE;
REINDEX DATABASE comolor_pos_production;

-- Update table statistics
ANALYZE;

-- Check for bloat
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Scaling Strategies

### 1. Read Replicas

```bash
# Set up read replica for reporting
pg_basebackup -h master_host -D /var/lib/postgresql/replica -U replication -P -W -R

# Configure replica
echo "standby_mode = 'on'" >> /var/lib/postgresql/replica/recovery.conf
echo "primary_conninfo = 'host=master_host port=5432 user=replication'" >> /var/lib/postgresql/replica/recovery.conf
```

### 2. Horizontal Partitioning

```sql
-- Partition large tables by shop_id ranges
CREATE TABLE sales_partition_1_100 PARTITION OF sales
    FOR VALUES FROM (1) TO (100);

CREATE TABLE sales_partition_101_200 PARTITION OF sales
    FOR VALUES FROM (101) TO (200);
```

This multi-tenant database design provides secure data isolation, good performance, and scalability for the Comolor POS system while maintaining cost efficiency.