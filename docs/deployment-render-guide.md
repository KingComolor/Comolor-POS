# Deployment to Render Guide

## Overview

This guide covers deploying the Comolor POS system to Render.com, a modern cloud platform that offers seamless deployment for web applications with PostgreSQL database support.

## Prerequisites

### Render Account Setup
1. Create account at [render.com](https://render.com)
2. Connect your GitHub repository
3. Verify email address
4. Add payment method (for PostgreSQL database)

### Repository Preparation
1. Ensure your code is in a GitHub repository
2. Repository must be public or you need Render Pro
3. All required files must be committed and pushed

## Database Setup

### PostgreSQL Database on Render

1. **Create Database Service**
   - Go to Render Dashboard
   - Click "New +" → "PostgreSQL"
   - Configure database:
     - **Name**: `comolor-pos-db`
     - **Database**: `comolor_pos`
     - **User**: `comolor_user`
     - **Region**: Choose closest to your users
     - **PostgreSQL Version**: 15 (recommended)
     - **Plan**: Start with Free tier for testing

2. **Database Configuration**
   ```
   Database Name: comolor_pos
   Username: comolor_user
   Password: [auto-generated]
   Host: [provided by Render]
   Port: 5432
   ```

3. **Connection Details**
   Render provides these connection strings:
   - **Internal Database URL**: For application connection
   - **External Database URL**: For external tools
   - **PSQL Command**: For direct database access

## Web Service Deployment

### Service Configuration

1. **Create Web Service**
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Select your repository and branch

2. **Basic Settings**
   ```
   Name: comolor-pos
   Region: Same as database
   Branch: main (or your production branch)
   Runtime: Python 3
   ```

3. **Build and Deploy Settings**
   ```
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn --bind 0.0.0.0:$PORT main:app
   ```

### Environment Variables

Configure these environment variables in Render:

#### Required Variables
```bash
# Database Connection
DATABASE_URL=[Your PostgreSQL database URL from Render]

# Application Security
SESSION_SECRET=[Generate random 32-character string]

# Flask Configuration
FLASK_ENV=production
PYTHONPATH=/opt/render/project/src

# MPesa Configuration (if using MPesa)
MPESA_CONSUMER_KEY=[Your MPesa consumer key]
MPESA_CONSUMER_SECRET=[Your MPesa consumer secret]
MPESA_SHORTCODE=[Your business shortcode]
MPESA_PASSKEY=[Your MPesa passkey]
MPESA_ENVIRONMENT=production
```

#### Optional Variables
```bash
# Logging
LOG_LEVEL=INFO

# Application Settings
APP_NAME=Comolor POS
APP_VERSION=1.0.0
```

### Deployment Files

#### requirements.txt
Ensure your requirements.txt includes all dependencies:
```txt
Flask==3.1.1
Flask-Login==0.6.2
Flask-SQLAlchemy==3.0.5
SQLAlchemy==2.0.41
psycopg2-binary==2.9.7
gunicorn==23.0.0
Werkzeug==3.1.3
email-validator==2.0.0
reportlab==4.0.4
requests==2.31.0
```

#### render.yaml (Optional)
Create `render.yaml` for infrastructure as code:
```yaml
services:
  - type: web
    name: comolor-pos
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn --bind 0.0.0.0:$PORT main:app
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: comolor-pos-db
          property: connectionString
      - key: SESSION_SECRET
        generateValue: true
      - key: FLASK_ENV
        value: production

databases:
  - name: comolor-pos-db
    databaseName: comolor_pos
    user: comolor_user
```

## Deployment Process

### Step-by-Step Deployment

1. **Prepare Repository**
   ```bash
   # Ensure all files are committed
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Create Database Service**
   - Create PostgreSQL database first
   - Note the connection string provided
   - Wait for database to be ready (usually 2-3 minutes)

3. **Create Web Service**
   - Select repository and branch
   - Configure build and start commands
   - Add environment variables
   - Deploy

4. **Monitor Deployment**
   - Watch build logs for errors
   - Check application logs after deployment
   - Test application functionality

### Initial Data Setup

After successful deployment, initialize your database:

```bash
# Connect to your database using Render's PSQL command
psql [external_database_url]

# Verify tables were created
\dt

# Check if demo data was loaded
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM shops;
```

## Post-Deployment Configuration

### Domain Setup

1. **Custom Domain (Optional)**
   - Go to service settings
   - Add custom domain
   - Configure DNS records:
     ```
     Type: CNAME
     Name: yourdomain.com
     Value: your-service.onrender.com
     ```

2. **SSL Certificate**
   - Render provides free SSL certificates
   - Automatically configured for custom domains
   - Certificate auto-renewal included

### Security Hardening

1. **Environment Variables**
   ```bash
   # Generate secure session secret
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Database Security**
   - Use connection pooling
   - Enable SSL connections
   - Regular security updates

3. **Application Security**
   ```python
   # Ensure HTTPS in production
   if os.environ.get('RENDER'):
       app.config['PREFERRED_URL_SCHEME'] = 'https'
   ```

## Monitoring and Maintenance

### Application Monitoring

1. **Render Metrics**
   - CPU and memory usage
   - Response times
   - Error rates
   - Request volume

2. **Database Monitoring**
   - Connection count
   - Query performance
   - Storage usage
   - Backup status

3. **Custom Logging**
   ```python
   import logging
   
   # Configure logging for production
   if os.environ.get('RENDER'):
       logging.basicConfig(
           level=logging.INFO,
           format='%(asctime)s %(levelname)s %(name)s %(message)s'
       )
   ```

### Backup Strategy

1. **Database Backups**
   - Render automatically backs up PostgreSQL
   - Daily backups retained for 7 days
   - Point-in-time recovery available

2. **Application Backups**
   - Code backed up in Git repository
   - Environment variables documented
   - Configuration stored in render.yaml

### Scaling

1. **Vertical Scaling**
   - Upgrade service plan for more CPU/RAM
   - Scale database for more connections
   - Monitor resource usage

2. **Horizontal Scaling**
   - Not available on Render free tier
   - Use load balancers for multiple instances
   - Consider database connection pooling

## Troubleshooting

### Common Deployment Issues

1. **Build Failures**
   ```bash
   # Check requirements.txt
   pip install -r requirements.txt

   # Verify Python version compatibility
   python --version
   ```

2. **Database Connection Issues**
   ```python
   # Test database connection
   import psycopg2
   
   try:
       conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
       print("Database connection successful")
   except Exception as e:
       print(f"Database connection failed: {e}")
   ```

3. **Environment Variable Issues**
   ```bash
   # Check environment variables in Render dashboard
   # Verify variable names match your code
   # Ensure sensitive values are properly set
   ```

### Application Issues

1. **Static Files Not Loading**
   ```python
   # Ensure static files are properly configured
   app = Flask(__name__, static_folder='static')
   ```

2. **Database Tables Not Created**
   ```python
   # Add table creation to app initialization
   with app.app_context():
       db.create_all()
   ```

3. **Session Issues**
   ```python
   # Verify session secret is set
   if not app.secret_key:
       raise ValueError("SESSION_SECRET environment variable must be set")
   ```

### Performance Issues

1. **Slow Database Queries**
   ```sql
   -- Add indexes for better performance
   CREATE INDEX idx_products_shop_id ON products(shop_id);
   CREATE INDEX idx_sales_created_at ON sales(created_at);
   ```

2. **Memory Usage**
   - Monitor application memory usage
   - Optimize database queries
   - Consider upgrading service plan

3. **Response Times**
   - Enable gzip compression
   - Optimize database connections
   - Cache frequently accessed data

## Maintenance Tasks

### Regular Updates

1. **Dependency Updates**
   ```bash
   # Update requirements.txt regularly
   pip list --outdated
   pip install --upgrade package_name
   ```

2. **Security Updates**
   - Monitor security advisories
   - Update dependencies promptly
   - Review Render security notifications

3. **Database Maintenance**
   ```sql
   -- Regular maintenance queries
   VACUUM ANALYZE;
   REINDEX DATABASE comolor_pos;
   ```

### Monitoring Checklist

- [ ] Application response times < 2 seconds
- [ ] Database connections within limits
- [ ] Error rates < 1%
- [ ] SSL certificates valid
- [ ] Backups completing successfully
- [ ] Environment variables secure
- [ ] Dependencies up to date

## Cost Optimization

### Free Tier Limitations
- Web service sleeps after 15 minutes of inactivity
- 750 hours per month (approximately 1 month)
- PostgreSQL free tier has connection limits

### Paid Plans
- **Starter Plan**: $7/month for web service
- **PostgreSQL**: $7/month for basic plan
- **Custom Domain**: Free with paid plans

### Cost Monitoring
- Monitor usage in Render dashboard
- Set up billing alerts
- Optimize resource usage

This guide ensures a successful deployment of your Comolor POS system to Render with proper configuration, monitoring, and maintenance procedures.