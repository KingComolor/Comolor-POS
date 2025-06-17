# Comolor POS Development Setup Guide

## Overview

This guide covers everything you need to know for developing, deploying, and packaging the Comolor POS system.

## Local Development Setup

### Prerequisites

1. **Python 3.11+**
2. **PostgreSQL 12+**
3. **Node.js 18+ (for desktop app)**
4. **Git**

### Environment Setup

1. **Clone and Setup Project**
```bash
git clone <your-repo-url>
cd comolor-pos
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Variables**
Create `.env` file:
```env
# Database
DATABASE_URL=postgresql://username:password@localhost/comolor_pos
PGHOST=localhost
PGPORT=5432
PGUSER=username
PGPASSWORD=password
PGDATABASE=comolor_pos

# Security
SESSION_SECRET=your-secret-key-here
SECRET_KEY=your-flask-secret-key

# MPesa Configuration (Production)
MPESA_ENVIRONMENT=production
MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
MPESA_PASSKEY=your-passkey
MPESA_SHORTCODE=your-shortcode

# MPesa Configuration (Sandbox - for testing)
MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY=sandbox-consumer-key
MPESA_CONSUMER_SECRET=sandbox-consumer-secret
MPESA_PASSKEY=sandbox-passkey
MPESA_SHORTCODE=sandbox-shortcode
```

5. **Database Setup**
```bash
# Create database
createdb comolor_pos

# Run the application (it will create tables automatically)
python main.py
```

### Development Commands

```bash
# Start development server
python main.py

# Start with Gunicorn (production-like)
gunicorn --bind 0.0.0.0:5000 --reload main:app

# Database operations (if needed)
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Project Structure

```
comolor-pos/
├── app.py                 # Main Flask application
├── main.py               # Application entry point
├── models.py             # Database models
├── production_config.py  # Production configuration
├── requirements.txt      # Python dependencies
├── routes/              # Route blueprints
│   ├── auth.py         # Authentication routes
│   ├── cashier.py      # POS terminal routes
│   ├── shop_admin.py   # Shop management routes
│   ├── super_admin.py  # System administration
│   └── mpesa.py        # Payment processing
├── static/             # Static assets
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript files
│   └── images/        # Image assets
├── templates/          # HTML templates
├── desktop_app_control.py      # Desktop app management
├── desktop_control_system.py   # Desktop control API
└── docs/              # Documentation
```

## Testing

### Manual Testing Checklist

1. **Authentication System**
   - [ ] User registration
   - [ ] Login/logout
   - [ ] Password change
   - [ ] Role-based access

2. **POS Operations**
   - [ ] Product search
   - [ ] Barcode scanning
   - [ ] Cart management
   - [ ] Cash payments
   - [ ] MPesa payments
   - [ ] Receipt printing

3. **Shop Management**
   - [ ] Product CRUD operations
   - [ ] Category management
   - [ ] Inventory tracking
   - [ ] Sales reporting
   - [ ] User management

4. **Super Admin Functions**
   - [ ] Shop management
   - [ ] License management
   - [ ] System settings
   - [ ] User oversight

### MPesa Testing

For sandbox testing:
1. Use Safaricom sandbox credentials
2. Test phone numbers: 254708374149, 254700000000
3. Test amounts: Use small amounts (1-100 KES)

## Common Development Issues

### Database Connection Issues
```bash
# Check PostgreSQL status
systemctl status postgresql

# Reset database
dropdb comolor_pos
createdb comolor_pos
python main.py  # Recreates tables
```

### MPesa Integration Issues
1. Verify credentials in `.env`
2. Check callback URLs are accessible
3. Test with sandbox environment first
4. Monitor logs for callback responses

### Session Issues
```bash
# Generate new session secret
python -c "import secrets; print(secrets.token_hex(32))"
```

## Security Considerations

### Before Production
1. **Change Default Credentials**
   - Update default admin password
   - Generate strong session secrets
   - Configure HTTPS certificates

2. **Environment Variables**
   - Never commit `.env` files
   - Use secure secret management
   - Rotate keys regularly

3. **Database Security**
   - Use strong passwords
   - Enable SSL connections
   - Regular backups
   - Limit database access

4. **Application Security**
   - Enable CSRF protection
   - Validate all inputs
   - Sanitize user data
   - Regular security updates

## Performance Optimization

### Database Optimization
1. Add indexes for frequently queried fields
2. Use connection pooling
3. Implement query optimization
4. Regular maintenance tasks

### Application Optimization
1. Enable caching for static assets
2. Compress responses
3. Optimize database queries
4. Monitor memory usage

## Monitoring and Logging

### Production Logging
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('/var/log/comolor-pos/app.log'),
        logging.StreamHandler()
    ]
)
```

### Key Metrics to Monitor
1. Response times
2. Error rates
3. Database performance
4. MPesa transaction success rates
5. User activity patterns

## Backup Strategy

### Database Backups
```bash
# Daily backup
pg_dump -h localhost -U username comolor_pos > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h localhost -U username -d comolor_pos < backup_20250617.sql
```

### Application Backups
1. Code repository (Git)
2. Configuration files
3. Static assets
4. Log files

## Development Best Practices

1. **Code Quality**
   - Follow PEP 8 style guide
   - Use meaningful variable names
   - Add comments for complex logic
   - Write docstrings for functions

2. **Version Control**
   - Commit frequently with clear messages
   - Use feature branches
   - Tag releases
   - Keep history clean

3. **Testing**
   - Test all new features
   - Test error scenarios
   - Validate with real data
   - Performance testing

4. **Documentation**
   - Keep documentation updated
   - Document API changes
   - Maintain changelog
   - User guides for new features

## Troubleshooting

### Common Errors

1. **"Module not found" errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database connection errors**
   - Check PostgreSQL is running
   - Verify credentials in .env
   - Check firewall settings

3. **MPesa callback errors**
   - Verify callback URLs
   - Check network connectivity
   - Review MPesa credentials

4. **Session errors**
   - Clear browser cookies
   - Regenerate session secret
   - Check session configuration

### Debug Mode

Enable debug mode for development:
```python
app.debug = True
```

Never enable debug mode in production.

## Next Steps

After setting up development environment:
1. Review the deployment guide for Render hosting
2. Check desktop app packaging guide
3. Test all functionality with real data
4. Configure production environment variables
5. Set up monitoring and logging