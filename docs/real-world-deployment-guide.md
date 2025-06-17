# Real World Deployment Setup Guide

## Overview

This guide covers deploying the Comolor POS system in real-world production environments, including cloud providers, VPS servers, and on-premises infrastructure with enterprise-grade security and scalability.

## Production Architecture

### Recommended Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Load Balancer │────│  Application     │────│   Database      │
│   (Nginx/HAProxy│    │  Servers         │    │   (PostgreSQL)  │
│   SSL Termination│    │  (Multiple       │    │   (Primary +    │
│   Rate Limiting) │    │   Instances)     │    │    Replica)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────┴────────┐             │
         │              │   File Storage   │             │
         └──────────────│   (Static Files, │─────────────┘
                        │    Receipts)     │
                        └─────────────────┘
```

### Infrastructure Components
- **Load Balancer**: SSL termination, traffic distribution
- **Application Servers**: Multiple Flask instances behind load balancer
- **Database**: PostgreSQL with read replicas for scaling
- **File Storage**: Static files, receipt storage, backups
- **Monitoring**: Application and infrastructure monitoring
- **Backup System**: Automated backups with retention policies

## Cloud Provider Deployments

### AWS Deployment

#### Infrastructure Setup
```yaml
# docker-compose.yml for AWS ECS
version: '3.8'
services:
  web:
    image: comolor-pos:latest
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=${RDS_DATABASE_URL}
      - SESSION_SECRET=${SESSION_SECRET}
      - MPESA_CONSUMER_KEY=${MPESA_CONSUMER_KEY}
      - MPESA_CONSUMER_SECRET=${MPESA_CONSUMER_SECRET}
    depends_on:
      - redis
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
```

#### AWS Services Configuration
```bash
# RDS PostgreSQL Database
aws rds create-db-instance \
  --db-instance-identifier comolor-pos-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --allocated-storage 20 \
  --db-name comolor_pos \
  --master-username admin \
  --master-user-password [secure-password]

# ECS Cluster
aws ecs create-cluster --cluster-name comolor-pos-cluster

# Application Load Balancer
aws elbv2 create-load-balancer \
  --name comolor-pos-alb \
  --subnets subnet-12345 subnet-67890 \
  --security-groups sg-12345
```

#### Security Groups
```bash
# Database Security Group
aws ec2 create-security-group \
  --group-name comolor-db-sg \
  --description "Database access for Comolor POS"

# Allow PostgreSQL from application servers only
aws ec2 authorize-security-group-ingress \
  --group-id sg-database \
  --protocol tcp \
  --port 5432 \
  --source-group sg-application
```

### Google Cloud Platform (GCP)

#### Cloud Run Deployment
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
```

```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/PROJECT_ID/comolor-pos
gcloud run deploy comolor-pos \
  --image gcr.io/PROJECT_ID/comolor-pos \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL,SESSION_SECRET=$SESSION_SECRET
```

#### Cloud SQL PostgreSQL
```bash
# Create Cloud SQL instance
gcloud sql instances create comolor-pos-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database and user
gcloud sql databases create comolor_pos --instance=comolor-pos-db
gcloud sql users create comolor_user --instance=comolor-pos-db --password=[secure-password]
```

### DigitalOcean Deployment

#### Droplet Setup
```bash
# Create Ubuntu 22.04 droplet with at least 2GB RAM
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Production Docker Setup
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  web:
    build: .
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://comolor_user:${DB_PASSWORD}@db:5432/comolor_pos
      - SESSION_SECRET=${SESSION_SECRET}
      - FLASK_ENV=production
    depends_on:
      - db
      - redis
    networks:
      - app-network
    
  db:
    image: postgres:15
    restart: unless-stopped
    environment:
      - POSTGRES_DB=comolor_pos
      - POSTGRES_USER=comolor_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - app-network
    
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks:
      - app-network
    
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/ssl/certs
      - static_files:/app/static
    depends_on:
      - web
    networks:
      - app-network

volumes:
  postgres_data:
  static_files:

networks:
  app-network:
    driver: bridge
```

## On-Premises Deployment

### Server Requirements

#### Minimum Hardware Requirements
```
- CPU: 4 cores (2.4GHz or higher)
- RAM: 8GB (16GB recommended)
- Storage: 100GB SSD (500GB recommended)
- Network: 100Mbps dedicated connection
- OS: Ubuntu 22.04 LTS or CentOS 8
```

#### Recommended Production Hardware
```
- CPU: 8 cores (3.0GHz or higher)
- RAM: 32GB
- Storage: 1TB NVMe SSD
- Network: 1Gbps connection with redundancy
- UPS: Uninterruptible power supply
- Backup: Separate backup storage system
```

### Ubuntu Server Setup

#### System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib nginx redis-server git curl

# Create application user
sudo useradd -m -s /bin/bash comolor
sudo usermod -aG sudo comolor

# Create application directory
sudo mkdir -p /opt/comolor-pos
sudo chown comolor:comolor /opt/comolor-pos
```

#### PostgreSQL Setup
```bash
# Secure PostgreSQL installation
sudo -u postgres psql

-- Create database and user
CREATE DATABASE comolor_pos;
CREATE USER comolor_user WITH ENCRYPTED PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE comolor_pos TO comolor_user;
ALTER USER comolor_user CREATEDB;
\q

# Configure PostgreSQL
sudo nano /etc/postgresql/15/main/postgresql.conf
# Update: listen_addresses = '*'
# Update: max_connections = 200

sudo nano /etc/postgresql/15/main/pg_hba.conf
# Add: host comolor_pos comolor_user 127.0.0.1/32 md5

sudo systemctl restart postgresql
```

#### Application Deployment
```bash
# Switch to application user
sudo su - comolor

# Clone repository
cd /opt/comolor-pos
git clone [your-repository-url] .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cat > .env << EOF
DATABASE_URL=postgresql://comolor_user:secure_password_here@localhost/comolor_pos
SESSION_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
FLASK_ENV=production
MPESA_CONSUMER_KEY=your_mpesa_key
MPESA_CONSUMER_SECRET=your_mpesa_secret
MPESA_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
MPESA_ENVIRONMENT=production
EOF

# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

#### Systemd Service Setup
```bash
# Create systemd service file
sudo tee /etc/systemd/system/comolor-pos.service << EOF
[Unit]
Description=Comolor POS Application
After=network.target postgresql.service

[Service]
Type=exec
User=comolor
Group=comolor
WorkingDirectory=/opt/comolor-pos
Environment=PATH=/opt/comolor-pos/venv/bin
EnvironmentFile=/opt/comolor-pos/.env
ExecStart=/opt/comolor-pos/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --timeout 120 main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable comolor-pos
sudo systemctl start comolor-pos
```

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/comolor-pos
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/your-domain.com.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }

    location /static/ {
        alias /opt/comolor-pos/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Security Configuration

### SSL/TLS Setup

#### Let's Encrypt (Free SSL)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Commercial SSL Certificate
```bash
# Generate private key and CSR
openssl req -new -newkey rsa:2048 -nodes -keyout your-domain.com.key -out your-domain.com.csr

# Install certificate files
sudo cp your-domain.com.crt /etc/ssl/certs/
sudo cp your-domain.com.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/your-domain.com.key
```

### Firewall Configuration
```bash
# UFW firewall setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow from [your-ip-address] to any port 22
sudo ufw enable

# For database access from specific IPs only
sudo ufw allow from [app-server-ip] to any port 5432
```

### Database Security
```sql
-- Create read-only user for reporting
CREATE USER comolor_readonly WITH ENCRYPTED PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE comolor_pos TO comolor_readonly;
GRANT USAGE ON SCHEMA public TO comolor_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO comolor_readonly;

-- Enable SSL for database connections
ALTER SYSTEM SET ssl = on;
SELECT pg_reload_conf();
```

## Monitoring and Maintenance

### System Monitoring

#### Install Monitoring Tools
```bash
# Install monitoring stack
sudo apt install prometheus node-exporter grafana

# Configure Prometheus
sudo tee /etc/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'comolor-pos'
    static_configs:
      - targets: ['localhost:5000']
  
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
      
  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:9187']
EOF
```

#### Application Monitoring
```python
# Add to your Flask app
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

# Custom metrics
from prometheus_client import Counter, Histogram

SALE_COUNTER = Counter('sales_total', 'Total number of sales')
SALE_AMOUNT = Histogram('sale_amount', 'Sale amounts')

# In your sale processing code
SALE_COUNTER.inc()
SALE_AMOUNT.observe(sale.total_amount)
```

### Backup Strategy

#### Database Backups
```bash
#!/bin/bash
# /opt/comolor-pos/scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/comolor-pos"
DB_NAME="comolor_pos"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U comolor_user -d $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Application files backup
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C /opt/comolor-pos \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  .

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

# Upload to cloud storage (optional)
aws s3 sync $BACKUP_DIR s3://your-backup-bucket/comolor-pos/
```

#### Automated Backup Cron Job
```bash
# Add to crontab
sudo crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/comolor-pos/scripts/backup.sh >> /var/log/comolor-backup.log 2>&1

# Weekly full system backup
0 3 * * 0 tar -czf /backups/system_backup_$(date +\%Y\%m\%d).tar.gz /opt/comolor-pos /etc/nginx /etc/systemd/system/comolor-pos.service
```

### Performance Optimization

#### Database Optimization
```sql
-- Create performance indexes
CREATE INDEX CONCURRENTLY idx_sales_shop_date ON sales(shop_id, created_at);
CREATE INDEX CONCURRENTLY idx_products_shop_active ON products(shop_id, is_active);
CREATE INDEX CONCURRENTLY idx_users_shop_active ON users(shop_id, user_active);

-- Configure PostgreSQL for production
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_segments = 32;
ALTER SYSTEM SET wal_buffers = '16MB';
SELECT pg_reload_conf();
```

#### Application Optimization
```python
# Redis caching configuration
import redis
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': 'localhost',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_DB': 0,
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Cache frequently accessed data
@cache.memoize(timeout=3600)
def get_shop_products(shop_id):
    return Product.query.filter_by(shop_id=shop_id, is_active=True).all()
```

### Disaster Recovery

#### Recovery Procedures
```bash
# Database recovery from backup
gunzip -c /backups/comolor-pos/db_backup_20250616_020000.sql.gz | psql -h localhost -U comolor_user -d comolor_pos

# Application recovery
cd /opt/comolor-pos
tar -xzf /backups/comolor-pos/app_backup_20250616_020000.tar.gz

# Restart services
sudo systemctl restart comolor-pos nginx postgresql
```

#### High Availability Setup
```bash
# PostgreSQL streaming replication
# On primary server
sudo -u postgres psql -c "CREATE USER replicator REPLICATION LOGIN CONNECTION LIMIT 1 ENCRYPTED PASSWORD 'replication_password';"

# Configure pg_hba.conf for replication
echo "host replication replicator [replica-ip]/32 md5" >> /etc/postgresql/15/main/pg_hba.conf

# On replica server
pg_basebackup -h [primary-ip] -D /var/lib/postgresql/15/main -U replicator -P -v -R -W -C -S replica1
```

This comprehensive deployment guide ensures your Comolor POS system runs reliably in production environments with enterprise-grade security, monitoring, and disaster recovery capabilities.