# Deploy Comolor POS to Render - Complete Guide

## Step 1: Prepare Your Repository

### 1. Create GitHub Repository
```bash
git init
git add .
git commit -m "Initial Comolor POS commit"
git remote add origin https://github.com/yourusername/comolor-pos.git
git push -u origin main
```

### 2. Configure for Render
Copy `render_requirements.txt` to `requirements.txt`:
```bash
cp render_requirements.txt requirements.txt
```

## Step 2: Database Setup on Render

### Option A: Render PostgreSQL (Recommended)
1. Go to Render Dashboard → New → PostgreSQL
2. Configure:
   - **Name**: `comolor-pos-db`
   - **Database**: `comolor_pos_production`
   - **User**: `comolor_admin`
   - **Region**: Choose closest to your users
   - **Plan**: Starter ($7/month)

### Option B: External Database (Alternative)
Use services like:
- **Supabase**: Free PostgreSQL with 500MB
- **ElephantSQL**: Free 20MB PostgreSQL
- **AWS RDS**: Pay-as-you-use

## Step 3: Deploy Web Service

### 1. Create Web Service
1. Go to Render Dashboard → New → Web Service
2. Connect your GitHub repository
3. Configure:
   - **Name**: `comolor-pos-app`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT main:app`

### 2. Environment Variables
Add these in Render Dashboard → Service → Environment:

**Required Variables:**
```
DATABASE_URL=postgresql://user:pass@host:5432/comolor_pos_production
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production
```

**MPesa Variables:**
```
MPESA_ENVIRONMENT=production
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_PASSKEY=your_passkey
MPESA_SHORTCODE=your_shortcode
```

### 3. Get Database Connection String
From your PostgreSQL service:
1. Go to PostgreSQL service → Connect
2. Copy "External Database URL"
3. Paste as `DATABASE_URL` in web service

## Step 4: Database Migration

### 1. Run Initial Migration
After first deployment, access your app URL and it will:
- Create all tables automatically
- Set up default super admin (admin/admin123)
- Create demo shop with sample data

### 2. Production Data Setup
```sql
-- Connect to your database via Render dashboard
-- Or use external tool like pgAdmin

-- Create production super admin
INSERT INTO users (username, email, password_hash, role, user_active) 
VALUES ('your_admin', 'your_email@domain.com', 'hashed_password', 'super_admin', true);

-- Update super admin phone for license payments
UPDATE system_settings 
SET value = '0797237383' 
WHERE key = 'license_payment_phone';
```

## Step 5: Custom Domain Setup

### 1. Add Custom Domain
1. In Render Dashboard → Service → Settings
2. Add custom domain: `yourpos.com`
3. Configure DNS records:
   ```
   Type: CNAME
   Name: @
   Value: your-service.onrender.com
   ```

### 2. SSL Certificate
- Render provides free SSL automatically
- Certificate auto-renews

## Step 6: Monitoring & Maintenance

### 1. Health Checks
Render automatically monitors:
- HTTP health checks on `/health`
- Service restarts on failures
- Uptime monitoring

### 2. Logs & Debugging
```bash
# View logs in Render Dashboard
# Or access via API
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.render.com/v1/services/YOUR_SERVICE_ID/logs
```

### 3. Scaling
- **Starter Plan**: 512MB RAM, 0.1 CPU
- **Standard Plan**: 2GB RAM, 1 CPU
- **Pro Plan**: 4GB RAM, 2 CPU

## Step 7: Cost Breakdown

### Monthly Costs:
- **PostgreSQL**: $7/month (Starter)
- **Web Service**: $7/month (Starter)
- **Custom Domain**: Free
- **SSL Certificate**: Free
- **Total**: $14/month

### Free Tier Option:
- Use Supabase (free PostgreSQL)
- Render free tier web service
- **Total**: $0/month (with limitations)

## Step 8: Production Optimizations

### 1. Environment Configuration
```python
# In app.py, add production config
if os.environ.get('FLASK_ENV') == 'production':
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
```

### 2. Database Indexing
```sql
-- Add indexes for better performance
CREATE INDEX idx_sales_shop_created ON sales(shop_id, created_at);
CREATE INDEX idx_products_shop_active ON products(shop_id, is_active);
CREATE INDEX idx_mpesa_transaction_id ON mpesa_transactions(transaction_id);
```

### 3. Redis Caching (Optional)
Add Redis service for session storage and caching:
1. Render Dashboard → New → Redis
2. Add `REDIS_URL` environment variable
3. Configure Flask-Session to use Redis

## Database Connection Examples

### Render PostgreSQL
```
DATABASE_URL=postgresql://comolor_admin:password@dpg-abc123-a.oregon-postgres.render.com/comolor_pos_production
```

### Supabase
```
DATABASE_URL=postgresql://postgres:password@db.abc123.supabase.co:5432/postgres
```

### ElephantSQL
```
DATABASE_URL=postgres://user:pass@ruby.db.elephantsql.com:5432/database
```

## Troubleshooting

### Common Issues:

**1. Database Connection Errors**
- Check DATABASE_URL format
- Verify database service is running
- Check firewall/security group settings

**2. Environment Variables**
- Ensure all required variables are set
- Check for typos in variable names
- Verify SECRET_KEY is set

**3. Migration Errors**
- Check database permissions
- Verify schema matches models
- Run migrations manually if needed

**4. MPesa Integration**
- Verify webhook URLs are accessible
- Check MPesa credentials are correct
- Ensure HTTPS is enabled for production

### Support Resources:
- Render Documentation: https://render.com/docs
- Community Support: Render Community Forum
- Direct Support: support@render.com