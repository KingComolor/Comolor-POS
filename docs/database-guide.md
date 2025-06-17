# Database Guide - Multi-Tenant PostgreSQL

## Overview

The Comolor POS system uses a multi-tenant PostgreSQL database architecture where each shop operates as a separate tenant while sharing the same database instance. This guide covers creation, implementation, usage, and maintenance.

## Database Architecture

### Multi-Tenant Design
- **Single Database**: All shops share one PostgreSQL database
- **Shop Isolation**: Data is isolated by shop_id foreign keys
- **Shared Resources**: Common tables (users, system_settings) serve all tenants
- **Scalable**: Supports unlimited shops without creating separate databases

### Core Tables Structure

```sql
-- Users table (shared across system)
users (id, username, email, password_hash, role, shop_id, user_active, created_at, last_login)

-- Shops table (tenant definition)
shops (id, name, owner_name, email, phone, address, till_number, license_expires, is_active, created_at, settings)

-- Shop-specific tables (isolated by shop_id)
products (id, name, price, stock_quantity, shop_id, category_id, ...)
categories (id, name, shop_id, created_at)
sales (id, receipt_number, shop_id, cashier_id, total_amount, ...)
sale_items (id, sale_id, product_id, quantity, unit_price, line_total)
```

## Database Creation & Setup

### Initial Setup
1. **Create PostgreSQL Database**
   ```bash
   createdb comolor_pos
   ```

2. **Set Environment Variables**
   ```bash
   export DATABASE_URL="postgresql://username:password@localhost/comolor_pos"
   export PGHOST=localhost
   export PGPORT=5432
   export PGUSER=username
   export PGPASSWORD=password
   export PGDATABASE=comolor_pos
   ```

3. **Initialize Tables**
   ```python
   # Run in Flask application context
   from app import app, db
   with app.app_context():
       db.create_all()
   ```

### Database Configuration
```python
# app.py configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
```

## Implementation Details

### Multi-Tenant Query Patterns
```python
# Always filter by shop_id for tenant isolation
products = Product.query.filter_by(shop_id=current_user.shop_id).all()

# Sales queries with shop isolation
sales = Sale.query.filter_by(shop_id=current_user.shop_id).order_by(Sale.created_at.desc()).all()

# Category management per shop
categories = Category.query.filter_by(shop_id=current_user.shop_id).all()
```

### Data Isolation Enforcement
```python
# Decorator to ensure shop access
@require_shop_access
def get_products():
    # Automatically filters by user's shop_id
    return Product.query.filter_by(shop_id=current_user.shop_id).all()
```

## User Usage

### Shop Admin Operations
1. **Product Management**
   - Add/edit products within their shop
   - Manage categories specific to their shop
   - View inventory reports for their shop only

2. **Sales Management**
   - View sales history for their shop
   - Process refunds for their shop's transactions
   - Generate reports for their shop data

3. **Staff Management**
   - Add cashiers to their specific shop
   - Manage user permissions within shop boundaries

### Cashier Operations
1. **POS Transactions**
   - Access only products from their assigned shop
   - Process sales that automatically link to their shop
   - View only their own transaction history

2. **Inventory Checks**
   - Check stock levels for their shop's products
   - Receive low stock alerts for their shop only

## Database Maintenance

### Regular Maintenance Tasks

1. **Performance Monitoring**
   ```sql
   -- Check connection count
   SELECT count(*) FROM pg_stat_activity;
   
   -- Monitor slow queries
   SELECT query, mean_exec_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_exec_time DESC LIMIT 10;
   ```

2. **Index Maintenance**
   ```sql
   -- Key indexes for performance
   CREATE INDEX idx_products_shop_id ON products(shop_id);
   CREATE INDEX idx_sales_shop_id ON sales(shop_id);
   CREATE INDEX idx_sales_created_at ON sales(created_at);
   CREATE INDEX idx_users_shop_id ON users(shop_id);
   ```

3. **Data Cleanup**
   ```sql
   -- Archive old sales data (older than 2 years)
   DELETE FROM sales WHERE created_at < NOW() - INTERVAL '2 years';
   
   -- Clean up inactive users (disabled for 6+ months)
   DELETE FROM users WHERE user_active = false AND last_login < NOW() - INTERVAL '6 months';
   ```

### Security Considerations

1. **Access Control**
   - Use strong database passwords
   - Limit database user permissions
   - Enable SSL connections in production

2. **Data Encryption**
   ```sql
   -- Enable row-level security for sensitive data
   ALTER TABLE users ENABLE ROW LEVEL SECURITY;
   ```

3. **Audit Logging**
   - All sensitive operations logged in audit_logs table
   - IP address and user agent tracking
   - Automatic log rotation and archival

This multi-tenant approach ensures data isolation, scalability, and efficient resource usage while maintaining security and performance for all shops in the system.