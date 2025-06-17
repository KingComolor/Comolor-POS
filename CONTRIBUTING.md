# Contributing to Comolor POS

Thank you for your interest in contributing to Comolor POS! This guide will help you get started with contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Development Guidelines](#development-guidelines)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Git
- Basic knowledge of Flask and SQLAlchemy
- Understanding of POS systems and payment processing

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/comolor-pos.git
   cd comolor-pos
   ```

2. **Set Up Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. **Database Setup**
   ```bash
   createdb comolor_pos_dev
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

4. **Run Development Server**
   ```bash
   gunicorn --bind 0.0.0.0:5000 --reload main:app
   ```

## Contributing Process

### 1. Issue First
- Check existing issues before creating new ones
- For new features, create an issue to discuss the approach
- For bugs, provide detailed reproduction steps

### 2. Branch Strategy
```bash
# Create feature branch
git checkout -b feature/add-inventory-alerts

# Create bugfix branch
git checkout -b bugfix/fix-mpesa-callback

# Create hotfix branch
git checkout -b hotfix/security-patch
```

### 3. Commit Messages
Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Examples:
```bash
feat(inventory): add low stock alerts
fix(mpesa): resolve callback timeout issue
docs(api): update endpoint documentation
refactor(auth): improve session management
```

## Coding Standards

### Python Code Style
- Follow PEP 8 style guide
- Use meaningful variable and function names
- Maximum line length: 88 characters
- Use type hints where appropriate

```python
# Good
def calculate_total_amount(items: List[SaleItem]) -> Decimal:
    """Calculate total amount for sale items."""
    return sum(item.line_total for item in items)

# Avoid
def calc_total(items):
    return sum(i.line_total for i in items)
```

### Flask Best Practices
- Use blueprints for route organization
- Implement proper error handling
- Use form validation
- Follow RESTful API principles

```python
# Good
@shop_admin.route('/products', methods=['GET'])
@require_role('shop_admin')
def list_products():
    try:
        products = Product.query.filter_by(shop_id=current_user.shop_id).all()
        return render_template('shop_admin/products.html', products=products)
    except Exception as e:
        flash('Error loading products', 'error')
        return redirect(url_for('shop_admin.dashboard'))
```

### Database Guidelines
- Use descriptive table and column names
- Include proper foreign key constraints
- Add indexes for performance
- Use migrations for schema changes

```python
# Good model definition
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    shop = db.relationship('Shop', backref='products')
```

### Frontend Guidelines
- Use semantic HTML
- Follow Bootstrap conventions
- Implement responsive design
- Use Feather icons consistently
- Maintain blue-purple gradient theme

```html
<!-- Good structure -->
<div class="card">
    <div class="card-header">
        <h5><i data-feather="package"></i> Product Information</h5>
    </div>
    <div class="card-body">
        <!-- Content -->
    </div>
</div>
```

### JavaScript Standards
- Use modern ES6+ syntax
- Implement proper error handling
- Use window prompts for user interactions
- Follow modular programming

```javascript
// Good
class ProductManager {
    constructor() {
        this.products = [];
        this.init();
    }
    
    async loadProducts() {
        try {
            const response = await fetch('/api/products');
            if (!response.ok) throw new Error('Failed to load products');
            this.products = await response.json();
        } catch (error) {
            window.alert('Error loading products: ' + error.message);
        }
    }
}
```

## Testing Guidelines

### Unit Tests
```python
import pytest
from app import app, db
from models import User, Shop

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_user_creation(client):
    user = User(username='testuser', email='test@example.com')
    db.session.add(user)
    db.session.commit()
    
    assert user.id is not None
    assert user.username == 'testuser'
```

### Integration Tests
```python
def test_product_creation_flow(client):
    # Login as shop admin
    response = client.post('/auth/login', data={
        'username': 'shopadmin',
        'password': 'shop123'
    })
    
    # Create product
    response = client.post('/shop_admin/products/add', data={
        'name': 'Test Product',
        'price': '10.00',
        'category_id': 1
    })
    
    assert response.status_code == 302  # Redirect after success
```

## Pull Request Process

### Before Submitting
1. **Test Your Changes**
   ```bash
   # Run tests
   python -m pytest
   
   # Check code style
   flake8 .
   
   # Test manually
   python main.py
   ```

2. **Update Documentation**
   - Update relevant documentation files
   - Add docstrings to new functions
   - Update API documentation if needed

3. **Commit History**
   ```bash
   # Clean up commits
   git rebase -i HEAD~3
   
   # Ensure commits are logical and well-described
   git log --oneline
   ```

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

## Issue Reporting

### Bug Reports
Include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details
- Screenshots if applicable

### Feature Requests
Include:
- Problem description
- Proposed solution
- Alternative solutions considered
- Implementation considerations

## Development Guidelines

### Security Considerations
- Validate all user inputs
- Use parameterized queries
- Implement proper authentication
- Log security events
- Follow OWASP guidelines

### Performance Best Practices
- Use database indexes appropriately
- Implement pagination for large datasets
- Optimize database queries
- Use caching where beneficial
- Monitor application performance

### MPesa Integration
- Test thoroughly in sandbox environment
- Handle all callback scenarios
- Implement proper error handling
- Log all transactions
- Follow Safaricom guidelines

### Multi-tenancy
- Ensure data isolation between shops
- Test with multiple shop scenarios
- Validate permissions properly
- Consider scalability implications

## Release Process

### Version Numbering
Follow semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes, backward compatible

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] Database migrations tested
- [ ] Deployment tested

## Getting Help

### Communication Channels
- Email: dev@comolor.com
- Issues: GitHub issues for bugs and features
- Documentation: Check docs/ directory first

### Development Resources
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Bootstrap Documentation](https://getbootstrap.com/docs/)
- [MPesa API Documentation](https://developer.safaricom.co.ke/)

Thank you for contributing to Comolor POS!