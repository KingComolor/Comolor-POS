# Dependencies Guide

## Overview

This guide covers all dependencies used in the Comolor POS system, including their purposes, versions, security considerations, and update procedures.

## Core Dependencies

### Flask Framework
```
Flask==3.1.1
```
**Purpose**: Core web framework for the application
**Features Used**:
- Request routing and handling
- Template rendering with Jinja2
- Session management
- Blueprint organization
- WSGI application interface

**Security Notes**:
- Regular updates required for security patches
- Debug mode disabled in production
- Secret key properly configured

### Database Layer

#### SQLAlchemy ORM
```
SQLAlchemy==2.0.41
Flask-SQLAlchemy==3.0.5
```
**Purpose**: Database abstraction and ORM
**Features Used**:
- Model definitions and relationships
- Query building and execution
- Connection pooling
- Migration support
- Multi-tenant data isolation

**Configuration**:
```python
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
```

#### PostgreSQL Driver
```
psycopg2-binary==2.9.7
```
**Purpose**: PostgreSQL database adapter
**Features Used**:
- Binary package for easy installation
- Connection pooling support
- SSL connection support
- Prepared statement caching

**Alternatives**:
- `psycopg2` (source package, requires compilation)
- `asyncpg` (for async applications)

### Authentication & Security

#### Flask-Login
```
Flask-Login==0.6.2
```
**Purpose**: User session management
**Features Used**:
- User authentication state
- Session persistence
- Login/logout handling
- User loading callbacks
- Remember me functionality

#### Werkzeug Security
```
Werkzeug==3.1.3
```
**Purpose**: Password hashing and security utilities
**Features Used**:
- Password hashing with salt
- Secure cookie handling
- CSRF protection utilities
- Input validation helpers

**Usage**:
```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash password
password_hash = generate_password_hash(password)

# Verify password
is_valid = check_password_hash(password_hash, password)
```

### Email Validation
```
email-validator==2.0.0
```
**Purpose**: Email address validation
**Features Used**:
- Syntax validation
- Domain checking
- International domain support
- Disposable email detection

### PDF Generation
```
reportlab==4.0.4
```
**Purpose**: PDF receipt and report generation
**Features Used**:
- Receipt formatting
- Barcode generation
- Table layouts
- Custom fonts and styling

**Usage**:
```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Generate receipt PDF
def generate_receipt_pdf(sale_data):
    # Implementation in utils/reports.py
    pass
```

### HTTP Requests
```
requests==2.31.0
```
**Purpose**: External API communication
**Features Used**:
- MPesa API integration
- HTTP client functionality
- SSL/TLS support
- Request/response handling
- Timeout management

**Security Configuration**:
```python
import requests

# Always use HTTPS in production
response = requests.post(
    api_url,
    json=payload,
    headers=headers,
    timeout=30,
    verify=True  # Verify SSL certificates
)
```

### WSGI Server
```
gunicorn==23.0.0
```
**Purpose**: Production WSGI HTTP Server
**Features Used**:
- Multi-worker process management
- Graceful worker restarts
- Request timeout handling
- Static file serving
- Load balancing

**Production Configuration**:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 --reload main:app
```

## Development Dependencies

### Testing Framework
```
pytest==7.4.0
pytest-flask==1.2.0
pytest-cov==4.1.0
```
**Purpose**: Testing framework and coverage
**Usage**:
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Code Quality
```
flake8==6.0.0
black==23.7.0
isort==5.12.0
```
**Purpose**: Code formatting and linting
**Usage**:
```bash
# Format code
black .

# Sort imports
isort .

# Check code quality
flake8 .
```

## Frontend Dependencies (CDN)

### Bootstrap CSS Framework
```html
<!-- Bootstrap 5.3.0 -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
```
**Purpose**: Responsive UI framework
**Features Used**:
- Grid system and layouts
- Form components
- Navigation elements
- Modal dialogs
- Alert messages

### Feather Icons
```html
<!-- Feather Icons -->
<script src="https://unpkg.com/feather-icons"></script>
```
**Purpose**: Consistent iconography
**Features Used**:
- Scalable vector icons
- Consistent design language
- Lightweight implementation

### Audio Library
```html
<!-- Tone.js for audio feedback -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.7.77/Tone.js"></script>
```
**Purpose**: Audio feedback for POS interactions
**Features Used**:
- Barcode scan sounds
- Payment confirmation sounds
- Error notification sounds

## Environment-Specific Dependencies

### Development Only
```
python-dotenv==1.0.0
```
**Purpose**: Environment variable management in development
**Usage**:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Production Monitoring
```
prometheus-flask-exporter==0.22.4
```
**Purpose**: Application metrics for monitoring
**Features**:
- Request metrics
- Response time tracking
- Error rate monitoring
- Custom business metrics

## Security Considerations

### Dependency Security Scanning
```bash
# Install security scanning tools
pip install safety bandit

# Check for known vulnerabilities
safety check

# Security code analysis
bandit -r app/
```

### Regular Updates
```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package_name

# Update all packages (with caution)
pip install --upgrade -r requirements.txt
```

### Pinned Versions
All dependencies are pinned to specific versions to ensure:
- Reproducible builds
- Consistent behavior across environments
- Controlled updates
- Security patch management

## Dependency Management

### Requirements Files Structure
```
requirements.txt          # Production dependencies
requirements-dev.txt      # Development dependencies
requirements-test.txt     # Testing dependencies
```

### Installation Commands
```bash
# Production environment
pip install -r requirements.txt

# Development environment
pip install -r requirements.txt -r requirements-dev.txt

# Testing environment
pip install -r requirements.txt -r requirements-test.txt
```

### Virtual Environment Management
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Deactivate virtual environment
deactivate

# Requirements generation
pip freeze > requirements.txt
```

## Version Compatibility

### Python Version Requirements
- **Minimum**: Python 3.9
- **Recommended**: Python 3.11
- **Tested**: Python 3.11.10

### Database Version Support
- **PostgreSQL**: 12.0 - 15.x
- **Recommended**: PostgreSQL 15.x

### Browser Compatibility
- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile**: iOS Safari 14+, Chrome Mobile 90+

## Update Procedures

### Patch Updates (x.x.X)
```bash
# Safe to update immediately
pip install --upgrade package_name==x.x.latest
```

### Minor Updates (x.X.x)
```bash
# Test in development first
pip install --upgrade package_name==x.latest.x
# Run full test suite
pytest
# Deploy to staging for testing
```

### Major Updates (X.x.x)
```bash
# Requires careful planning
# 1. Review changelog for breaking changes
# 2. Create feature branch
# 3. Update and test thoroughly
# 4. Update documentation
# 5. Plan deployment strategy
```

### Security Updates
```bash
# Apply security updates immediately
pip install --upgrade package_name==secure_version

# Verify application functionality
python -m pytest tests/

# Deploy to production ASAP
```

## Troubleshooting

### Common Issues

#### Installation Problems
```bash
# Clear pip cache
pip cache purge

# Reinstall package
pip uninstall package_name
pip install package_name

# Force reinstall
pip install --force-reinstall package_name
```

#### Version Conflicts
```bash
# Check dependency tree
pip show package_name

# Resolve conflicts
pip install pipdeptree
pipdeptree --packages package_name
```

#### Binary Package Issues
```bash
# For psycopg2 installation issues
sudo apt-get install libpq-dev python3-dev

# Alternative: use binary package
pip install psycopg2-binary
```

### Environment Issues
```bash
# Verify Python version
python --version

# Check installed packages
pip list

# Verify virtual environment
which python
```

## Best Practices

### Dependency Selection
1. **Prefer well-maintained packages** with active communities
2. **Use minimal dependencies** to reduce attack surface
3. **Choose packages with good documentation**
4. **Consider long-term support** and update frequency

### Security Practices
1. **Pin exact versions** in production
2. **Regular security audits** with safety and bandit
3. **Monitor security advisories** for dependencies
4. **Update promptly** when security issues are discovered

### Performance Considerations
1. **Profile dependency impact** on application startup
2. **Use binary packages** when available for production
3. **Consider dependency size** for deployment efficiency
4. **Monitor memory usage** of heavy dependencies

This comprehensive dependencies guide ensures proper management, security, and maintenance of all project dependencies.