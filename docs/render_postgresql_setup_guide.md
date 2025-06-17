# PostgreSQL Database Setup on Render

## Quick Setup Guide

### Step 1: Create Database
1. **Log into Render** at https://render.com
2. **Click "New +"** in the top navigation
3. **Select "PostgreSQL"** from the dropdown

### Step 2: Configure Database
**Database Name:** `comolor-pos-db` (or your preferred name)
**Database:** `comolor_pos` (the actual database name inside PostgreSQL)
**User:** `comolor_admin` (database username)
**Region:** Choose closest to your users:
- `oregon` (US West)
- `ohio` (US East) 
- `frankfurt` (Europe)
- `singapore` (Asia)

**Plan:** Start with **Free** ($0/month) for testing, upgrade to **Starter** ($7/month) for production

### Step 3: Database Settings
- **Version:** PostgreSQL 15 (latest stable)
- **Auto-suspend:** Leave enabled for free tier
- **Backup retention:** 7 days (free tier)

### Step 4: Get Connection Details
After creation, Render provides:
- **Internal Database URL:** Used by your app
- **External Database URL:** For external tools
- **Host, Port, Database, Username, Password:** Individual connection details

## Connection Information

### Internal URL (for your app)
```
postgresql://username:password@hostname:5432/database_name
```

### External URL (for database tools)
```
postgresql://username:password@hostname:5432/database_name?sslmode=require
```

## Environment Variables Setup

### For Web Service
When creating your web service, add these environment variables:

**Automatic (Recommended):**
```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: comolor-pos-db
      property: connectionString
```

**Manual:**
```
DATABASE_URL=postgresql://username:password@hostname:5432/database_name
```

## Database Management

### Using Render Dashboard
1. **Database Dashboard:** View metrics, logs, connection info
2. **Connect:** Built-in web SQL client
3. **Backups:** Manual backups and restore points
4. **Metrics:** CPU, memory, storage usage

### Using External Tools

**pgAdmin:**
- Host: `dpg-xxxxx-a.oregon-postgres.render.com`
- Port: `5432`
- Database: `comolor_pos`
- Username: `comolor_admin`
- Password: (from Render dashboard)
- SSL Mode: `Require`

**DBeaver:**
1. New Connection → PostgreSQL
2. Use external connection URL
3. Enable SSL

**Command Line:**
```bash
psql "postgresql://username:password@hostname:5432/database_name?sslmode=require"
```

## Database Initialization

Your Flask app will automatically create tables on first run:

```python
# In app.py
with app.app_context():
    import models  # Import all models
    db.create_all()  # Create tables
```

For manual setup:
```sql
-- Connect to database and run
CREATE TABLE shops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    -- ... other fields
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    -- ... other fields
);
-- Continue with other tables
```

## Production Considerations

### Upgrading Plans
**Free Tier Limitations:**
- Suspends after 90 days of inactivity
- 1 GB storage
- 97 connection limit

**Starter Plan ($7/month):**
- No suspension
- 10 GB storage
- 97 connections
- Daily backups

**Pro Plan ($20/month):**
- 100 GB storage
- 197 connections
- Point-in-time recovery

### Performance Optimization
```sql
-- Create indexes for your main queries
CREATE INDEX idx_products_shop_id ON products(shop_id);
CREATE INDEX idx_sales_shop_id ON sales(shop_id);
CREATE INDEX idx_sales_date ON sales(created_at);
```

### Backup Strategy
**Automatic Backups:**
- Render creates daily backups (Starter+ plans)
- 7-day retention on Starter
- 30-day retention on Pro

**Manual Backups:**
```bash
# Using pg_dump
pg_dump "postgresql://user:pass@host:5432/db?sslmode=require" > backup.sql

# Restore
psql "postgresql://user:pass@host:5432/db?sslmode=require" < backup.sql
```

## Security Settings

### Connection Security
- **SSL Required:** Always enabled on Render
- **Password Authentication:** Required
- **Network Isolation:** Database only accessible to your services

### Access Control
```sql
-- Create read-only user for reporting
CREATE USER readonly_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE comolor_pos TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

## Monitoring

### Render Dashboard Metrics
- **Connections:** Active/max connections
- **CPU Usage:** Database server load
- **Memory Usage:** RAM consumption
- **Storage:** Disk space used
- **Query Performance:** Slow query detection

### Custom Monitoring
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('comolor_pos')) as db_size;

-- Check table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check active connections
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';
```

## Troubleshooting

### Common Issues

**Connection Timeout:**
```python
# Add to production_config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

**Too Many Connections:**
```python
# Reduce connection pool size
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 5,
    'max_overflow': 10
}
```

**SSL Certificate Error:**
```python
# Ensure SSL is properly configured
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
```

### Support
- **Render Support:** Available through dashboard
- **Community:** Render Community Forum
- **Documentation:** https://render.com/docs/databases

This guide covers everything needed to set up and manage PostgreSQL on Render for your POS system.