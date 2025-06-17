# Deployment Guide - Comolor POS

This guide covers deployment options for the Comolor POS system on various platforms.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Local Deployment](#local-deployment)
- [Production Deployment](#production-deployment)
- [Render Deployment](#render-deployment)
- [Heroku Deployment](#heroku-deployment)
- [Docker Deployment](#docker-deployment)
- [Database Migration](#database-migration)
- [SSL Configuration](#ssl-configuration)
- [Monitoring & Maintenance](#monitoring--maintenance)

## Prerequisites

### System Requirements
- Python 3.11 or higher
- PostgreSQL 12 or higher
- 512MB RAM minimum (2GB recommended)
- 1GB disk space minimum
- SSL certificate for production

### Required Accounts
- Safaricom Daraja API account (for MPesa)
- Database hosting service
- Domain name (for production)

## Environment Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd comolor-pos
```

### 2. Environment Variables
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Security
SESSION_SECRET=your-32-character-secret-key

# MPesa Configuration
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
```

## Local Deployment

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Create database
createdb comolor_pos

# Initialize tables
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 3. Run Application
```bash
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

## Production Deployment

### General Production Setup

1. **Security Configuration**
   ```bash
   # Set production environment
   FLASK_ENV=production
   DEBUG=False
   
   # Generate secure session key
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Database Optimization**
   ```sql
   -- Create indexes for performance
   CREATE INDEX idx_sales_created_at ON sales(created_at);
   CREATE INDEX idx_products_shop_id ON products(shop_id);
   CREATE INDEX idx_users_shop_id ON users(shop_id);
   ```

3. **Web Server Configuration**
   ```bash
   # Gunicorn with multiple workers
   gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 main:app
   ```

## Render Deployment

### 1. Prepare Repository
```bash
# Ensure render.yaml is configured
cat render.yaml
```

### 2. Deploy to Render
1. Connect GitHub repository to Render
2. Create PostgreSQL database
3. Deploy web service
4. Configure environment variables

### 3. Post-Deployment
```bash
# Initialize database via Render shell
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Heroku Deployment

### 1. Heroku Setup
```bash
# Install Heroku CLI
heroku create comolor-pos

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set SESSION_SECRET=your-secret-key
heroku config:set MPESA_CONSUMER_KEY=your-key
```

### 2. Deploy
```bash
git push heroku main
heroku run python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Docker Deployment

### 1. Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
```

### 2. Docker Compose
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/comolor_pos
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: comolor_pos
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 3. Deploy
```bash
docker-compose up -d
```

## Database Migration

### Initial Setup
```bash
# Create all tables
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Schema Updates
```sql
-- Example migration script
-- Add new column to products table
ALTER TABLE products ADD COLUMN supplier_id INTEGER;

-- Add foreign key constraint
ALTER TABLE products ADD CONSTRAINT fk_products_supplier 
FOREIGN KEY (supplier_id) REFERENCES suppliers(id);
```

### Backup Before Migration
```bash
# PostgreSQL backup
pg_dump -h hostname -U username -d comolor_pos > backup_$(date +%Y%m%d).sql

# Restore if needed
psql -h hostname -U username -d comolor_pos < backup_20250616.sql
```

## SSL Configuration

### Nginx Configuration
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Let's Encrypt (Free SSL)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring & Maintenance

### Health Checks
```python
# Add to routes
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
```

### Log Management
```bash
# Logrotate configuration
sudo nano /etc/logrotate.d/comolor-pos

/var/log/comolor-pos/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    copytruncate
}
```

### Database Backup
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h $PGHOST -U $PGUSER $PGDATABASE > /backups/comolor_pos_$DATE.sql
gzip /backups/comolor_pos_$DATE.sql

# Keep only 30 days
find /backups -name "comolor_pos_*.sql.gz" -mtime +30 -delete
```

### Performance Monitoring
```bash
# Monitor database connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'comolor_pos';

# Monitor slow queries
SELECT query, mean_time, calls FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check connection string
   echo $DATABASE_URL
   
   # Test connection
   psql $DATABASE_URL -c "SELECT 1"
   ```

2. **MPesa Integration Issues**
   ```bash
   # Verify callback URLs are accessible
   curl -X POST https://yourdomain.com/mpesa/confirmation
   
   # Check MPesa credentials
   echo $MPESA_CONSUMER_KEY
   ```

3. **Memory Issues**
   ```bash
   # Monitor memory usage
   free -h
   
   # Reduce Gunicorn workers
   gunicorn --workers 2 main:app
   ```

### Performance Optimization

1. **Database Indexes**
   ```sql
   -- Add missing indexes
   CREATE INDEX CONCURRENTLY idx_sales_shop_created 
   ON sales(shop_id, created_at);
   ```

2. **Connection Pooling**
   ```python
   # In app.py
   app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
       "pool_size": 10,
       "pool_recycle": 300,
       "pool_pre_ping": True,
   }
   ```

## Security Checklist

- [ ] HTTPS enabled with valid SSL certificate
- [ ] Environment variables secured
- [ ] Database access restricted
- [ ] Regular security updates applied
- [ ] Firewall configured
- [ ] Backup strategy implemented
- [ ] Monitoring and alerting set up
- [ ] Rate limiting configured
- [ ] CSRF protection enabled

## Post-Deployment Verification

1. **Test Core Functions**
   - Login with demo accounts
   - Create a test sale
   - Process MPesa payment (sandbox)
   - Generate receipt
   - Verify inventory updates

2. **Monitor Logs**
   ```bash
   # Watch application logs
   tail -f /var/log/comolor-pos/app.log
   
   # Check for errors
   grep -i error /var/log/comolor-pos/app.log
   ```

3. **Performance Testing**
   ```bash
   # Simple load test
   ab -n 100 -c 10 https://yourdomain.com/
   ```

For additional support, refer to the troubleshooting section or contact comolor07@gmail.com.