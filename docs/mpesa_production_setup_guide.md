# MPesa Production Setup Guide

This guide explains how to obtain MPesa production credentials for real-world deployment of the Comolor POS system.

## Overview

For MPesa integration to work in production, you need two types of credentials:

1. **Super Admin Credentials** - For license payments to the main Comolor business
2. **Shop Owner Credentials** - For individual shop transactions

## Part 1: Super Admin MPesa Setup

### Prerequisites
- Registered business with valid KRA PIN
- Business registration documents
- Valid business bank account
- M-Pesa for Business account

### Step 1: Register M-Pesa for Business
1. Visit any Safaricom shop or agent
2. Fill out M-Pesa for Business application form
3. Provide required documents:
   - Business registration certificate
   - KRA PIN certificate
   - ID copy of business owner
   - Business permit/license
4. Get your **Business Till Number** (e.g., 123456)
5. Activate M-Pesa for Business account

### Step 2: Create Safaricom Developer Account
1. Go to [https://developer.safaricom.co.ke](https://developer.safaricom.co.ke)
2. Click "Sign Up" and create developer account
3. Verify your email address
4. Complete profile information

### Step 3: Create Production App
1. Login to developer portal
2. Click "Create New App"
3. Fill application details:
   - **App Name**: Comolor POS System
   - **Description**: Point of Sale system for license payments
   - **Environment**: Production
   - **Products**: Select "M-Pesa Express (STK Push)"
4. Submit application for review

### Step 4: Get Production Credentials
After approval (usually 2-5 business days):
1. Go to "My Apps" section
2. Click on your approved app
3. Note down these credentials:
   - **Consumer Key**: e.g., `ABC123xyz...`
   - **Consumer Secret**: e.g., `XYZ789abc...`
   - **Passkey**: e.g., `bfb279f9aa9bdbcf...`
   - **Shortcode**: Your business till number

### Step 5: Configure Callback URLs
1. In your app settings, configure:
   - **Validation URL**: `https://yourdomain.com/mpesa/c2b/validation`
   - **Confirmation URL**: `https://yourdomain.com/mpesa/c2b/confirmation`
   - **Timeout URL**: `https://yourdomain.com/mpesa/c2b/timeout`

### Step 6: Set Environment Variables
Add these to your production environment:
```bash
# Super Admin MPesa Credentials
MPESA_ENVIRONMENT=production
MPESA_CONSUMER_KEY=your_consumer_key_here
MPESA_CONSUMER_SECRET=your_consumer_secret_here
MPESA_PASSKEY=your_passkey_here
MPESA_SHORTCODE=your_till_number_here

# Super Admin Till for License Payments
SUPER_ADMIN_TILL_NUMBER=123456
SUPER_ADMIN_PHONE=254797237383
```

## Part 2: Shop Owner MPesa Setup

### For Each Shop Owner:

### Step 1: Business Registration
1. Register business with relevant authorities
2. Obtain KRA PIN certificate
3. Get business permit/license
4. Open business bank account

### Step 2: M-Pesa for Business Account
1. Visit Safaricom shop with documents:
   - Business registration certificate
   - KRA PIN certificate
   - ID copy of business owner
   - Business permit
2. Apply for M-Pesa for Business
3. Get unique **Till Number** (e.g., 654321)
4. Activate account and test with small transactions

### Step 3: Developer Account (Same as Super Admin)
1. Create account at [developer.safaricom.co.ke](https://developer.safaricom.co.ke)
2. Verify email and complete profile

### Step 4: Create Shop-Specific App
1. Create new app in developer portal:
   - **App Name**: [Shop Name] POS System
   - **Description**: Point of sale for [Shop Name]
   - **Environment**: Production
   - **Products**: M-Pesa Express (STK Push)
2. Submit for approval

### Step 5: Get Shop Credentials
After approval:
1. Consumer Key
2. Consumer Secret
3. Passkey
4. Shortcode (Till Number)

### Step 6: Configure in Comolor POS
Shop admin enters credentials in system settings:
1. Login as shop admin
2. Go to Settings > Payment Configuration
3. Enter MPesa credentials:
   - Consumer Key
   - Consumer Secret
   - Passkey
   - Till Number
4. Test connection

## Part 3: Production Deployment Configuration

### Environment Variables Structure
```bash
# Super Admin (Global)
MPESA_ENVIRONMENT=production
SUPER_ADMIN_MPESA_CONSUMER_KEY=abc123...
SUPER_ADMIN_MPESA_CONSUMER_SECRET=xyz789...
SUPER_ADMIN_MPESA_PASSKEY=passkey123...
SUPER_ADMIN_TILL_NUMBER=123456
SUPER_ADMIN_PHONE=254797237383

# Database for shop-specific credentials
# (Stored in shops table, encrypted)
```

### Database Schema for Shop Credentials
```sql
-- Add to shops table
ALTER TABLE shops ADD COLUMN mpesa_consumer_key VARCHAR(255);
ALTER TABLE shops ADD COLUMN mpesa_consumer_secret VARCHAR(255);
ALTER TABLE shops ADD COLUMN mpesa_passkey VARCHAR(255);
ALTER TABLE shops ADD COLUMN mpesa_shortcode VARCHAR(20);
ALTER TABLE shops ADD COLUMN mpesa_active BOOLEAN DEFAULT FALSE;
```

## Part 4: Testing and Validation

### Test Checklist for Super Admin:
- [ ] License payment from customer to super admin till
- [ ] Webhook receives confirmation
- [ ] License activation works
- [ ] Receipt generation functions

### Test Checklist for Shop Owner:
- [ ] Customer payment to shop till
- [ ] Real-time payment verification
- [ ] Transaction recorded in system
- [ ] Receipt printed/generated
- [ ] Inventory updated

## Part 5: Security Considerations

### Credential Security:
1. **Never** store credentials in plain text
2. Use environment variables for sensitive data
3. Encrypt shop credentials in database
4. Implement credential rotation policy
5. Use HTTPS for all callback URLs
6. Validate all webhook signatures

### Access Control:
1. Only shop admins can configure MPesa
2. Cashiers cannot view/edit credentials
3. Super admin can monitor all shops
4. Audit log all credential changes

## Part 6: Troubleshooting

### Common Issues:

**1. "Invalid Consumer Key"**
- Solution: Verify credentials are for production environment
- Check if app is approved for production use

**2. "Till Number Not Found"**
- Solution: Confirm till number is active
- Test with small transaction first

**3. "Callback URL Not Reachable"**
- Solution: Ensure HTTPS is enabled
- Check firewall/security settings
- Verify URL is publicly accessible

**4. "Transaction Timeout"**
- Solution: Customer may have cancelled
- Check customer's MPesa balance
- Verify till number is correct

### Support Contacts:
- **Safaricom Business Support**: 0722 002 200
- **Developer Support**: developer@safaricom.co.ke
- **Comolor Support**: comolor07@gmail.com

## Part 7: Go-Live Checklist

### Before Production:
- [ ] All credentials obtained and tested
- [ ] Webhook URLs configured and tested
- [ ] Security measures implemented
- [ ] Backup and recovery procedures ready
- [ ] Staff trained on new payment process
- [ ] Customer communication prepared
- [ ] Fallback procedures for system downtime

### Launch Day:
- [ ] Monitor transactions closely
- [ ] Test with small amounts first
- [ ] Have technical support ready
- [ ] Communicate with customers about new system
- [ ] Document any issues for resolution

### Post-Launch:
- [ ] Monitor transaction success rates
- [ ] Collect user feedback
- [ ] Optimize based on usage patterns
- [ ] Plan for scaling if needed

## Important Notes:

1. **Timeline**: Allow 2-3 weeks for complete setup including approvals
2. **Costs**: Safaricom charges transaction fees (typically 1-2% of transaction value)
3. **Compliance**: Ensure all business licenses are current
4. **Testing**: Always test thoroughly in sandbox before production
5. **Support**: Keep contact information for Safaricom business support

## Next Steps:

1. Start with super admin credentials setup
2. Train one shop owner on the process
3. Document lessons learned
4. Scale to remaining shops
5. Provide ongoing support and monitoring

For technical implementation details, refer to the MPesa Integration Guide in the docs folder.