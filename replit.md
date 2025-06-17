# Comolor POS System

## Overview

Comolor POS is a comprehensive Point of Sale system designed for Kenyan retailers. The application provides multi-tenant shop management with role-based access control, inventory management, sales processing, and MPesa payment integration.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Flask-Login with session-based authentication
- **Deployment**: Gunicorn WSGI server with autoscale deployment target

### Frontend Architecture
- **UI Framework**: Bootstrap 5.3.0 for responsive design
- **Icons**: Feather Icons for consistent iconography
- **JavaScript**: Vanilla JavaScript with modular components for POS functionality
- **Real-time Features**: AJAX-based product search and payment polling

### Database Design
- **Users**: Multi-role system (super_admin, shop_admin, cashier)
- **Shops**: Multi-tenant architecture with license management
- **Products**: Shop-specific inventory with categories and stock tracking
- **Sales**: Complete transaction tracking with line items
- **MPesa Integration**: Payment processing and transaction logging

## Key Components

### User Roles and Access Control
1. **Super Admin**: System-wide management, shop oversight, license administration
2. **Shop Admin**: Shop-specific management, product/inventory control, staff management
3. **Cashier**: POS interface access only, transaction processing

### Core Modules
1. **Authentication System** (`routes/auth.py`): Login, registration, password management
2. **POS Terminal** (`routes/cashier.py`): Product search, cart management, payment processing
3. **Shop Administration** (`routes/shop_admin.py`): Product management, inventory control, reporting
4. **Super Admin Panel** (`routes/super_admin.py`): System oversight, license management
5. **MPesa Integration** (`routes/mpesa.py`): Payment gateway callbacks and processing

### Frontend Components
1. **POS Interface** (`static/js/pos.js`): Shopping cart, product search, payment processing
2. **Barcode Scanner** (`static/js/barcode.js`): Hardware barcode scanner integration
3. **MPesa Integration** (`static/js/mpesa.js`): Payment status polling and UI updates

## Data Flow

### User Authentication Flow
1. User submits credentials via login form
2. System validates against database and checks shop license status
3. Session established with role-based redirects
4. Audit logging for security tracking

### Sales Transaction Flow
1. Cashier searches/scans products in POS interface
2. Products added to cart with real-time total calculations
3. Payment method selected (cash/MPesa)
4. Transaction recorded with inventory updates
5. Receipt generation and printing

### MPesa Payment Flow
1. Customer initiates MPesa payment to shop's till number
2. MPesa sends callback to system endpoint
3. System processes and matches payment to transaction
4. Real-time status updates via polling mechanism
5. Transaction completion and receipt generation

### License Management Flow
1. Shop registration creates inactive shop
2. License payment processed via MPesa
3. Super admin activates shop upon payment confirmation
4. Periodic license expiry checks and notifications

## External Dependencies

### Core Dependencies
- **Flask 3.1.1**: Web framework
- **SQLAlchemy 2.0.41**: Database ORM
- **psycopg2-binary**: PostgreSQL adapter
- **Flask-Login**: User session management
- **ReportLab**: PDF receipt generation
- **Requests**: HTTP client for external API calls

### Frontend Dependencies
- **Bootstrap 5.3.0**: CSS framework (CDN)
- **Feather Icons**: Icon library (CDN)

### Payment Integration
- **MPesa Daraja API**: For C2B payment processing
- Configuration via environment variables for API credentials

## Deployment Strategy

### Environment Configuration
- **Development**: Local development with debug mode enabled
- **Production**: Gunicorn deployment with autoscaling capabilities
- **Database**: PostgreSQL with connection pooling and health checks

### Infrastructure Requirements
- **Nix packages**: PostgreSQL, OpenSSL, FreeType, glibc locales
- **Python 3.11**: Runtime environment
- **Node.js 20**: For potential frontend tooling

### Security Considerations
- CSRF protection enabled on forms
- Password hashing with Werkzeug security
- Session-based authentication with secure cookies
- Audit logging for sensitive operations
- Environment-based configuration for secrets

### Scaling Architecture
- Multi-tenant design supports unlimited shops
- Database-driven configuration for shop-specific settings
- Stateless application design for horizontal scaling
- Background job capability for payment processing

## Changelog

```
Changelog:
- June 16, 2025. Initial setup
- June 16, 2025. Successfully migrated from Replit Agent to standard Replit environment
- June 16, 2025. Enhanced cashier settings with comprehensive POS device configuration options
- June 16, 2025. Added printer test functionality and connection checking capabilities
- June 16, 2025. Implemented advanced device settings including screen modes, audio controls, and timeout management
- June 16, 2025. Enhanced cart scrolling with smooth scroll behavior, visual indicators, and responsive design
- June 16, 2025. Fixed cart functionality issues and improved shortcuts UI with clear badge-based design
- June 16, 2025. Removed shortcuts panel and enhanced product card visibility with larger text and better spacing
- June 16, 2025. Completed migration from Replit Agent with improved cart scrolling, eliminated horizontal scrollbar issues, and enhanced product card visibility
- June 16, 2025. Confirmed blue-purple gradient theme consistency across entire system - all components now use unified #667eea to #764ba2 gradient styling
- June 16, 2025. Converted all embedded page navigation to window prompts - eliminated window.open, location.href redirects, and form submissions now use alert dialogs instead of page navigation
- June 16, 2025. Created comprehensive documentation suite including database guide, MPesa integration guide, user guide, developer guide, deployment guides, dependencies guide, and super admin guide
- June 16, 2025. Enhanced all POS features for real-world usage with comprehensive error handling, user feedback, and business logic
- June 16, 2025. Implemented complete POS system with inventory management, payment processing, receipt generation, and audit trails
- June 16, 2025. Added real-world MPesa integration with proper timeout handling, error recovery, and user guidance
- June 16, 2025. Enhanced barcode scanner functionality with comprehensive feedback and error handling for production use
- June 16, 2025. Successfully migrated from Replit Agent to standard Replit environment with PostgreSQL database and secure session management
- June 16, 2025. Implemented real-time MPesa payment integration with webhook validation, till-based payments for shops, and licensing payments to super admin phone (0797237383)
- June 17, 2025. Created comprehensive deployment and packaging documentation including development setup guide, Render deployment guide, desktop app packaging guide, and quick start checklist for production deployment
- June 17, 2025. Successfully migrated from Replit Agent to standard Replit environment - fixed missing utils module, resolved import errors, created PostgreSQL database, and updated homepage footer with 2025 Comolor copyright
- June 17, 2025. Enhanced homepage footer visibility with improved contrast, professional styling, better text hierarchy, and clear contact information formatting
- June 17, 2025. Updated homepage footer to use blue-purple gradient theme (#667eea to #764ba2) matching the system's consistent branding
- June 17, 2025. Updated contact information to comolor07@gmail.com and +254 797 237 383 for support and business communications
- June 17, 2025. Successfully completed migration from Replit Agent to standard Replit environment with PostgreSQL database setup and updated all contact information system-wide
- June 17, 2025. Created comprehensive screenshots page showcasing shop admin and cashier features with visual mockups and detailed feature descriptions
- June 17, 2025. Created complete MPesa production deployment documentation including setup guides for super admin and shop owners, system configuration guide, and quick reference materials
- June 17, 2025. Created comprehensive multi-tenant PostgreSQL database guides including database design, deployment strategies, security best practices, and quick start checklist for production deployment
- June 17, 2025. Successfully completed migration from Replit Agent to standard Replit environment - fixed Poetry package configuration, created PostgreSQL database, resolved Python path and import issues, and verified application runs correctly on port 5000
- June 17, 2025. Fixed shop admin management functions - updated product, cashier, and category templates to use proper POST form submissions for delete and toggle operations, replaced custom confirmation handlers with standard JavaScript confirm dialogs
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```