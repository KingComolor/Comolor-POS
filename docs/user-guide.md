# User Guide - Comolor POS System

## Overview

Comolor POS is a comprehensive point-of-sale system designed for Kenyan retailers. This guide explains how to use all features of the system for different user types.

## Getting Started

### Login Process
1. Open the Comolor POS application in your web browser
2. Enter your username and password
3. Click "Login" to access your dashboard
4. You'll be redirected based on your role (Super Admin, Shop Admin, or Cashier)

### Default Demo Accounts
- **Super Admin**: admin / admin123
- **Shop Admin**: shopadmin / shop123
- **Cashier**: cashier / cash123

## User Roles

### Super Admin
- Manage all shops in the system
- Activate/deactivate shops
- Approve license payments
- Manage system users
- View system-wide reports

### Shop Admin
- Manage their specific shop
- Add/edit products and categories
- Manage cashier accounts
- View sales reports
- Process refunds

### Cashier
- Process sales transactions
- Search for products
- Handle cash and MPesa payments
- Print receipts
- View transaction history

## Shop Admin Guide

### Dashboard
Your dashboard shows:
- Today's sales summary
- Low stock alerts
- Recent transactions
- Quick action buttons

### Product Management

#### Adding Products
1. Navigate to "Products" from the main menu
2. Click "Add Product" button
3. Fill in product details:
   - **Name**: Product name (required)
   - **Description**: Brief product description
   - **Price**: Selling price (required)
   - **Cost Price**: Purchase cost for profit tracking
   - **Barcode**: Product barcode (optional)
   - **SKU**: Stock keeping unit code
   - **Category**: Select from your categories
   - **Stock Quantity**: Initial stock amount
   - **Low Stock Alert**: Minimum quantity before alert
4. Click "Save Product"

#### Managing Categories
1. Go to "Categories" from the menu
2. Click "Add Category" to create new categories
3. Enter category name and save
4. Use categories to organize your products

#### Stock Management
- **View Stock Levels**: Check current inventory from Products page
- **Low Stock Alerts**: System highlights products below threshold
- **Stock Updates**: Automatic updates when sales are processed
- **Manual Adjustments**: Contact system admin for stock corrections

### Sales Management

#### Viewing Sales
1. Navigate to "Sales" from the main menu
2. View list of all transactions
3. Use filters to find specific sales:
   - Date range
   - Payment method
   - Cashier
   - Amount range

#### Processing Refunds
1. Find the sale to refund in Sales list
2. Click "Refund" button
3. Enter refund reason
4. Confirm refund
5. Stock quantities are automatically restored

### Staff Management

#### Adding Cashiers
1. Go to "Cashiers" from the menu
2. Click "Add Cashier"
3. Fill in cashier details:
   - Username (must be unique)
   - Email address
   - Password
   - Full name
4. Click "Save Cashier"
5. New cashier can now login and access POS

#### Managing Cashier Access
- **Activate/Deactivate**: Enable or disable cashier accounts
- **Password Reset**: Help cashiers reset forgotten passwords
- **Permission Control**: Cashiers can only access POS functions

### Reports and Analytics

#### Sales Reports
- **Daily Sales**: View today's transaction summary
- **Weekly/Monthly**: Extended period reports
- **Product Performance**: Best and worst selling items
- **Payment Methods**: Cash vs MPesa breakdown

#### Inventory Reports
- **Stock Levels**: Current inventory status
- **Low Stock**: Items needing restocking
- **Product Movement**: Track inventory changes
- **Profit Analysis**: Compare cost vs selling prices

## Cashier Guide

### Point of Sale (POS) Interface

#### Starting a Sale
1. Login to access the POS interface
2. The main screen shows:
   - Product search bar
   - Shopping cart
   - Category buttons
   - Payment options

#### Adding Products to Cart

##### By Search
1. Type product name in search bar
2. Select from dropdown results
3. Product adds to cart automatically

##### By Barcode
1. Click in barcode field or use barcode scanner
2. Scan product barcode
3. Product adds to cart with current price

##### By Category
1. Click category button
2. Browse products in that category
3. Click product to add to cart

#### Managing Cart
- **Quantity**: Click +/- buttons to adjust quantities
- **Remove Items**: Click X button to remove products
- **Clear Cart**: Use "Clear All" to empty cart
- **View Total**: Cart shows subtotal, tax, and total amount

#### Processing Payment

##### Cash Payment
1. Select "Cash" payment method
2. Enter amount received from customer
3. System calculates change due
4. Click "Complete Sale"
5. Print receipt

##### MPesa Payment
1. Select "MPesa" payment method
2. Enter customer phone number
3. Click "Request Payment"
4. Customer receives STK push on phone
5. Wait for payment confirmation
6. Print receipt when confirmed

#### Receipt Management
- **Print Receipt**: Automatic or manual printing
- **Reprint**: Access previous receipts for reprinting
- **Email Receipt**: Send receipt to customer email (if configured)

### POS Settings

#### Barcode Scanner Configuration
1. Go to Settings from POS interface
2. Configure scanner settings:
   - **Scanner Type**: USB or Bluetooth
   - **Scan Delay**: Time between scans
   - **Sound**: Enable/disable scan sounds
   - **Auto-add**: Automatically add scanned items

#### Receipt Printer Setup
1. Access printer settings
2. Configure:
   - **Printer Type**: Thermal or regular
   - **Paper Size**: 58mm or 80mm
   - **Print Quality**: Draft or normal
   - **Auto Print**: Automatic receipt printing

#### Display Settings
- **Screen Mode**: Fullscreen or windowed
- **Font Size**: Adjust for readability
- **Theme**: Choose color scheme
- **Language**: Select display language

## Customer Transactions

### Processing a Typical Sale

1. **Customer Arrives**: Greet customer and start new sale
2. **Add Products**: Scan barcodes or search for items
3. **Review Cart**: Verify all items and quantities are correct
4. **Apply Discounts**: If applicable, apply any discounts
5. **Choose Payment**: Customer selects cash or MPesa
6. **Process Payment**: Complete transaction based on method
7. **Print Receipt**: Provide receipt to customer
8. **Thank Customer**: Complete the interaction professionally

### Handling Special Situations

#### Returns and Exchanges
- Only Shop Admins can process refunds
- Note customer reason for return
- Check product condition
- Refer to Shop Admin for processing

#### Payment Issues
- **MPesa Delays**: Wait up to 2 minutes for confirmation
- **Insufficient Cash**: Calculate exact change needed
- **System Errors**: Contact Shop Admin immediately

#### Product Issues
- **Item Not Found**: Use manual search or contact Shop Admin
- **Price Discrepancies**: Verify with Shop Admin before sale
- **Out of Stock**: Inform customer and suggest alternatives

## System Features

### Real-time Updates
- **Stock Levels**: Updated instantly after each sale
- **Payment Status**: Live MPesa payment tracking
- **Sales Data**: Immediate reporting updates
- **User Activity**: Real-time audit logging

### Security Features
- **User Authentication**: Secure login system
- **Role-based Access**: Limited access based on user role
- **Audit Trail**: Complete activity logging
- **Data Encryption**: Secure data transmission
- **Session Management**: Automatic logout for security

### Mobile Responsiveness
- **Tablet Friendly**: Optimized for tablet POS systems
- **Phone Access**: Basic functions available on phones
- **Touch Interface**: Designed for touch screen devices
- **Offline Mode**: Limited functionality when internet is down

## Troubleshooting

### Common Issues

#### Login Problems
- **Forgot Password**: Contact Shop Admin for reset
- **Account Disabled**: Check with Shop Admin
- **Wrong Username**: Verify spelling and case sensitivity

#### POS Issues
- **Barcode Not Scanning**: Check scanner connection and settings
- **Printer Not Working**: Verify printer connection and paper
- **Slow Performance**: Close unnecessary browser tabs
- **Network Issues**: Check internet connection

#### Payment Problems
- **MPesa Not Working**: Verify phone number format (254...)
- **Payment Delayed**: Wait 2 minutes then check status
- **Wrong Amount**: Cancel and restart transaction

### Getting Help

#### Shop Admin Support
- Contact your Shop Admin for:
  - Account issues
  - Product problems
  - Refund requests
  - Technical difficulties

#### System Administrator
- Contact system admin for:
  - Shop setup issues
  - License problems
  - Major technical issues
  - System updates

### Best Practices

#### Daily Operations
- **Start of Day**: Check system status and printer
- **Regular Backups**: Ensure data is being saved
- **Stock Checks**: Monitor inventory levels
- **End of Day**: Review sales summary

#### Customer Service
- **Be Patient**: Help customers understand the process
- **Stay Professional**: Maintain courteous service
- **Know Your Products**: Understand what you're selling
- **Handle Issues Calmly**: Don't panic if problems occur

#### Security
- **Logout Properly**: Always logout when finished
- **Protect Passwords**: Don't share login credentials
- **Monitor Transactions**: Watch for unusual activity
- **Report Issues**: Immediately report any problems

This user guide helps you make the most of the Comolor POS system while providing excellent customer service and maintaining accurate business records.