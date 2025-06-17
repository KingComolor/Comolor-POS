#!/bin/bash
# Production Deployment Script for Comolor POS

set -e

echo "🚀 Starting Comolor POS Production Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="comolor-pos"
APP_DIR="/opt/comolor-pos"
SERVICE_FILE="/etc/systemd/system/comolor-pos.service"
NGINX_CONFIG="/etc/nginx/sites-available/comolor-pos"
LOG_DIR="/var/log/comolor-pos"
BACKUP_DIR="/var/backups/comolor-pos"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}" 
   exit 1
fi

# Create application user
echo -e "${YELLOW}Creating application user...${NC}"
useradd -r -s /bin/false comolor || echo "User already exists"

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p $APP_DIR $LOG_DIR $BACKUP_DIR
chown comolor:comolor $APP_DIR $LOG_DIR $BACKUP_DIR

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
apt update
apt install -y python3 python3-pip python3-venv postgresql-client nginx redis-server supervisor

# Setup Python environment
echo -e "${YELLOW}Setting up Python environment...${NC}"
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install Python dependencies
pip install gunicorn psycopg2-binary flask flask-sqlalchemy flask-login
pip install requests reportlab email-validator werkzeug sqlalchemy

# Copy application files
echo -e "${YELLOW}Copying application files...${NC}"
# Note: In real deployment, you'd copy from your git repo or upload
# cp -r /path/to/your/app/* $APP_DIR/
chown -R comolor:comolor $APP_DIR

# Create systemd service
echo -e "${YELLOW}Creating systemd service...${NC}"
cat > $SERVICE_FILE << EOF
[Unit]
Description=Comolor POS Application
After=network.target postgresql.service

[Service]
Type=notify
User=comolor
Group=comolor
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=FLASK_ENV=production
ExecStart=$APP_DIR/venv/bin/gunicorn --bind unix:$APP_DIR/comolor-pos.sock --workers 4 --timeout 120 --access-logfile $LOG_DIR/access.log --error-logfile $LOG_DIR/error.log main:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
echo -e "${YELLOW}Configuring Nginx...${NC}"
cat > $NGINX_CONFIG << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL configuration (you'll need to add your certificates)
    ssl_certificate /etc/ssl/certs/comolor-pos.crt;
    ssl_certificate_key /etc/ssl/private/comolor-pos.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Static files
    location /static {
        alias $APP_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Application
    location / {
        proxy_pass http://unix:$APP_DIR/comolor-pos.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # WebSocket support for real-time features
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # API endpoints for mobile/desktop apps
    location /api/ {
        proxy_pass http://unix:$APP_DIR/comolor-pos.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS for desktop apps
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization";
    }
}
EOF

# Enable Nginx site
ln -sf $NGINX_CONFIG /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Create backup script
echo -e "${YELLOW}Creating backup script...${NC}"
cat > /usr/local/bin/backup-comolor-pos << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/comolor-pos"
DATE=$(date +%Y%m%d_%H%M%S)
DATABASE_URL=$(grep DATABASE_URL /opt/comolor-pos/.env | cut -d '=' -f2)

# Database backup
pg_dump $DATABASE_URL > $BACKUP_DIR/database_$DATE.sql
gzip $BACKUP_DIR/database_$DATE.sql

# Application backup
tar -czf $BACKUP_DIR/app_$DATE.tar.gz -C /opt comolor-pos

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /usr/local/bin/backup-comolor-pos

# Setup cron for daily backups
echo "0 2 * * * root /usr/local/bin/backup-comolor-pos" >> /etc/crontab

# Create monitoring script
cat > /usr/local/bin/monitor-comolor-pos << 'EOF'
#!/bin/bash
# Simple monitoring script

LOG_FILE="/var/log/comolor-pos/monitor.log"
APP_URL="http://localhost"

# Check if service is running
if ! systemctl is-active --quiet comolor-pos; then
    echo "$(date): Service is down, attempting restart" >> $LOG_FILE
    systemctl restart comolor-pos
fi

# Check if app responds
if ! curl -f -s $APP_URL > /dev/null; then
    echo "$(date): App not responding, restarting service" >> $LOG_FILE
    systemctl restart comolor-pos
fi

# Check database connections
CONNECTIONS=$(sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='comolor_pos_production';" -t | xargs)
if [ "$CONNECTIONS" -gt 80 ]; then
    echo "$(date): High database connections: $CONNECTIONS" >> $LOG_FILE
fi
EOF

chmod +x /usr/local/bin/monitor-comolor-pos

# Setup monitoring cron (every 5 minutes)
echo "*/5 * * * * root /usr/local/bin/monitor-comolor-pos" >> /etc/crontab

# Enable and start services
echo -e "${YELLOW}Starting services...${NC}"
systemctl daemon-reload
systemctl enable comolor-pos
systemctl start comolor-pos
systemctl enable nginx
systemctl start nginx

# Create environment file template
cat > $APP_DIR/.env.example << EOF
# Production Environment Variables for Comolor POS

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/comolor_pos_production

# Security
SECRET_KEY=your-super-secret-key-here

# MPesa Configuration
MPESA_ENVIRONMENT=production
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_PASSKEY=your_passkey
MPESA_SHORTCODE=your_shortcode

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379/0

# Application Settings
FLASK_ENV=production
FLASK_DEBUG=False
EOF

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Copy your application files to $APP_DIR"
echo "2. Create $APP_DIR/.env with your configuration"
echo "3. Run database migrations"
echo "4. Configure SSL certificates"
echo "5. Set up domain DNS"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "- Check service status: systemctl status comolor-pos"
echo "- View logs: journalctl -u comolor-pos -f"
echo "- Restart service: systemctl restart comolor-pos"
echo "- Run backup: /usr/local/bin/backup-comolor-pos"