# API Documentation - Comolor POS

This document provides comprehensive documentation for all backend API endpoints in the Comolor POS system.

## Table of Contents
- [Authentication](#authentication)
- [User Management](#user-management)
- [Shop Management](#shop-management)
- [Product Management](#product-management)
- [Sales Processing](#sales-processing)
- [MPesa Integration](#mpesa-integration)
- [Reports & Analytics](#reports--analytics)
- [System Administration](#system-administration)

## Base URL
```
Production: https://yourdomain.com
Development: http://localhost:5000
```

## Authentication

All authenticated endpoints require a valid session. Authentication is session-based using Flask-Login.

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "super_admin",
    "shop_id": null
  },
  "redirect_url": "/super_admin/dashboard"
}
```

### Logout
```http
POST /auth/logout
```

**Response:**
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```

### Change Password
```http
POST /auth/change-password
Content-Type: application/x-www-form-urlencoded

current_password=oldpass&new_password=newpass&confirm_password=newpass
```

## User Management

### Get User Profile
```http
GET /api/user/profile
Authorization: Session Required
```

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "super_admin",
  "shop_id": null,
  "created_at": "2025-06-16T10:00:00Z",
  "last_login": "2025-06-16T14:00:00Z"
}
```

### Create User
```http
POST /super_admin/users/create
Authorization: Super Admin Required
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123",
  "role": "shop_admin",
  "shop_id": 1
}
```

**Response:**
```json
{
  "status": "success",
  "message": "User created successfully",
  "user_id": 5
}
```

## Shop Management

### List All Shops
```http
GET /super_admin/shops
Authorization: Super Admin Required
```

**Response:**
```json
{
  "shops": [
    {
      "id": 1,
      "name": "Demo Shop",
      "owner_name": "Shop Owner",
      "email": "shop@example.com",
      "phone": "+254700000000",
      "address": "Nairobi, Kenya",
      "till_number": "123456",
      "is_active": true,
      "license_expires": "2025-07-16T00:00:00Z",
      "created_at": "2025-06-16T10:00:00Z"
    }
  ]
}
```

### Create Shop
```http
POST /super_admin/shops/create
Authorization: Super Admin Required
Content-Type: application/json

{
  "name": "New Shop",
  "owner_name": "John Doe",
  "email": "john@example.com",
  "phone": "+254700000001",
  "address": "Mombasa, Kenya",
  "till_number": "789012"
}
```

### Toggle Shop Status
```http
POST /super_admin/shops/{shop_id}/toggle
Authorization: Super Admin Required
```

**Response:**
```json
{
  "status": "success",
  "message": "Shop status updated",
  "is_active": true
}
```

## Product Management

### List Products
```http
GET /shop_admin/products
Authorization: Shop Admin Required
```

**Query Parameters:**
- `page` (optional): Page number for pagination
- `per_page` (optional): Items per page (default: 20)
- `category` (optional): Filter by category ID
- `search` (optional): Search term for product name

**Response:**
```json
{
  "products": [
    {
      "id": 1,
      "name": "Coca Cola 500ml",
      "description": "Refreshing soft drink",
      "price": "50.00",
      "cost_price": "35.00",
      "barcode": "123456789012",
      "sku": "COKE500",
      "stock_quantity": 100,
      "low_stock_threshold": 10,
      "category_id": 1,
      "category_name": "Beverages",
      "is_active": true,
      "created_at": "2025-06-16T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "pages": 3
  }
}
```

### Create Product
```http
POST /shop_admin/products/create
Authorization: Shop Admin Required
Content-Type: application/json

{
  "name": "New Product",
  "description": "Product description",
  "price": "25.00",
  "cost_price": "15.00",
  "barcode": "987654321098",
  "sku": "PROD001",
  "stock_quantity": 50,
  "low_stock_threshold": 5,
  "category_id": 1
}
```

### Update Product
```http
PUT /shop_admin/products/{product_id}
Authorization: Shop Admin Required
Content-Type: application/json

{
  "name": "Updated Product Name",
  "price": "30.00",
  "stock_quantity": 75
}
```

### Delete Product
```http
DELETE /shop_admin/products/{product_id}
Authorization: Shop Admin Required
```

**Response:**
```json
{
  "status": "success",
  "message": "Product deleted successfully"
}
```

### Search Products (POS)
```http
GET /cashier/products/search
Authorization: Cashier Required

Query Parameters:
- q: Search term
- barcode: Barcode lookup
```

**Response:**
```json
{
  "products": [
    {
      "id": 1,
      "name": "Coca Cola 500ml",
      "price": "50.00",
      "stock_quantity": 100,
      "barcode": "123456789012"
    }
  ]
}
```

### Get Product by Barcode
```http
GET /cashier/product/barcode/{barcode}
Authorization: Cashier Required
```

**Response:**
```json
{
  "id": 1,
  "name": "Coca Cola 500ml",
  "price": "50.00",
  "stock_quantity": 100,
  "barcode": "123456789012"
}
```

## Sales Processing

### Create Sale
```http
POST /cashier/sale/create
Authorization: Cashier Required
Content-Type: application/json

{
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "unit_price": "50.00"
    },
    {
      "product_id": 2,
      "quantity": 1,
      "unit_price": "25.00"
    }
  ],
  "payment_method": "cash",
  "amount_received": "150.00",
  "change_given": "25.00",
  "customer_phone": "+254700000000",
  "customer_name": "John Customer"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Sale completed successfully",
  "sale_id": 123,
  "receipt_number": "RCP-20250616-123",
  "total_amount": "125.00",
  "change_given": "25.00"
}
```

### Get Sale Details
```http
GET /cashier/sale/{sale_id}
Authorization: Cashier Required
```

**Response:**
```json
{
  "id": 123,
  "receipt_number": "RCP-20250616-123",
  "subtotal": "125.00",
  "tax_amount": "20.00",
  "total_amount": "145.00",
  "payment_method": "cash",
  "customer_phone": "+254700000000",
  "customer_name": "John Customer",
  "status": "completed",
  "created_at": "2025-06-16T14:30:00Z",
  "items": [
    {
      "product_id": 1,
      "product_name": "Coca Cola 500ml",
      "quantity": 2,
      "unit_price": "50.00",
      "line_total": "100.00"
    }
  ]
}
```

### List Sales
```http
GET /shop_admin/sales
Authorization: Shop Admin Required
```

**Query Parameters:**
- `page` (optional): Page number
- `start_date` (optional): Filter from date (YYYY-MM-DD)
- `end_date` (optional): Filter to date (YYYY-MM-DD)
- `cashier_id` (optional): Filter by cashier
- `payment_method` (optional): Filter by payment method

**Response:**
```json
{
  "sales": [
    {
      "id": 123,
      "receipt_number": "RCP-20250616-123",
      "total_amount": "145.00",
      "payment_method": "cash",
      "cashier_name": "John Cashier",
      "created_at": "2025-06-16T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
```

### Refund Sale
```http
POST /shop_admin/sales/{sale_id}/refund
Authorization: Shop Admin Required
Content-Type: application/json

{
  "reason": "Customer return - defective product",
  "refund_amount": "50.00"
}
```

## MPesa Integration

### Check Payment Status
```http
GET /cashier/mpesa/check/{sale_id}
Authorization: Cashier Required
```

**Response:**
```json
{
  "payment_received": true,
  "payment_data": {
    "transaction_id": "MPesa123456",
    "amount": "145.00",
    "phone": "254700000000",
    "transaction_time": "2025-06-16T14:35:00Z"
  }
}
```

### Confirm Payment
```http
POST /cashier/mpesa/confirm/{sale_id}
Authorization: Cashier Required
```

**Response:**
```json
{
  "status": "success",
  "message": "Payment confirmed successfully",
  "receipt_number": "RCP-20250616-123"
}
```

### MPesa Callbacks (Webhook Endpoints)

#### C2B Confirmation
```http
POST /mpesa/confirmation
Content-Type: application/json

{
  "TransactionType": "Pay Bill",
  "TransID": "MPesa123456",
  "TransTime": "20250616143500",
  "TransAmount": "145.00",
  "BusinessShortCode": "123456",
  "BillRefNumber": "RCP-20250616-123",
  "InvoiceNumber": "",
  "OrgAccountBalance": "10000.00",
  "ThirdPartyTransID": "",
  "MSISDN": "254700000000",
  "FirstName": "JOHN",
  "MiddleName": "",
  "LastName": "CUSTOMER"
}
```

#### C2B Validation
```http
POST /mpesa/validation
Content-Type: application/json

{
  "TransactionType": "Pay Bill",
  "TransID": "MPesa123456",
  "TransTime": "20250616143500",
  "TransAmount": "145.00",
  "BusinessShortCode": "123456",
  "BillRefNumber": "RCP-20250616-123",
  "MSISDN": "254700000000",
  "FirstName": "JOHN",
  "LastName": "CUSTOMER"
}
```

**Response:**
```json
{
  "ResultCode": 0,
  "ResultDesc": "Accepted"
}
```

## Reports & Analytics

### Sales Summary
```http
GET /shop_admin/reports/sales-summary
Authorization: Shop Admin Required
```

**Query Parameters:**
- `period`: daily, weekly, monthly, yearly
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)

**Response:**
```json
{
  "period": "daily",
  "start_date": "2025-06-16",
  "end_date": "2025-06-16",
  "summary": {
    "total_sales": "2500.00",
    "total_transactions": 25,
    "average_transaction": "100.00",
    "cash_sales": "1500.00",
    "mpesa_sales": "1000.00"
  },
  "daily_breakdown": [
    {
      "date": "2025-06-16",
      "sales": "2500.00",
      "transactions": 25
    }
  ]
}
```

### Product Performance
```http
GET /shop_admin/reports/product-performance
Authorization: Shop Admin Required
```

**Response:**
```json
{
  "top_products": [
    {
      "product_id": 1,
      "product_name": "Coca Cola 500ml",
      "quantity_sold": 50,
      "revenue": "2500.00",
      "profit": "750.00"
    }
  ],
  "low_stock": [
    {
      "product_id": 5,
      "product_name": "Product Name",
      "current_stock": 3,
      "threshold": 10
    }
  ]
}
```

## System Administration

### System Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-16T14:00:00Z",
  "database": "connected",
  "version": "1.0.0"
}
```

### Audit Logs
```http
GET /super_admin/audit-logs
Authorization: Super Admin Required
```

**Query Parameters:**
- `page`: Page number
- `user_id`: Filter by user
- `action`: Filter by action type
- `start_date`: Start date
- `end_date`: End date

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "user_id": 1,
      "username": "admin",
      "action": "user_login",
      "entity_type": "user",
      "entity_id": 1,
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2025-06-16T14:00:00Z"
    }
  ]
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "price",
      "issue": "Must be a positive number"
    }
  }
}
```

### Common Error Codes
- `AUTHENTICATION_REQUIRED`: 401 - User not authenticated
- `PERMISSION_DENIED`: 403 - Insufficient permissions
- `RESOURCE_NOT_FOUND`: 404 - Requested resource not found
- `VALIDATION_ERROR`: 400 - Input validation failed
- `SHOP_INACTIVE`: 403 - Shop license expired or inactive
- `INSUFFICIENT_STOCK`: 400 - Not enough inventory
- `PAYMENT_FAILED`: 400 - Payment processing error

## Rate Limiting

API endpoints are rate limited to prevent abuse:
- Authentication endpoints: 5 requests per minute
- General API endpoints: 100 requests per minute
- MPesa callbacks: No limit (authenticated by Safaricom)

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## API Versioning

Current API version: v1
Version is included in response headers:
```
X-API-Version: 1.0
```

For breaking changes, new versions will be introduced with URL versioning:
```
/api/v2/endpoint
```

## Testing

### Test Endpoints
Development environment includes test endpoints:

```http
POST /test/create-sample-data
Authorization: Development Only
```

```http
POST /test/reset-database
Authorization: Development Only
```

### Sandbox Mode
For MPesa integration testing, use sandbox credentials and the special test endpoints:

```http
POST /mpesa/test/simulate-payment
Content-Type: application/json

{
  "amount": "100.00",
  "phone": "254700000000",
  "bill_ref": "TEST123"
}
```