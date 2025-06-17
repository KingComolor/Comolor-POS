# MPesa Production Setup - Quick Reference

## For Super Admin (Comolor Business)

### Required Information
- **Business**: Comolor POS System
- **Phone**: +254 797 237 383
- **Till**: Get from Safaricom Business registration
- **Purpose**: License fee collection

### Steps Summary
1. Register M-Pesa for Business → Get Till Number
2. Create Safaricom Developer Account → developer.safaricom.co.ke
3. Create Production App → Get Consumer Key, Secret, Passkey
4. Configure in System Settings → Test license payments

## For Shop Owners

### Before You Start
- Business must be registered
- Need KRA PIN certificate
- Business bank account required
- Valid business license/permit

### Required from Safaricom
1. **M-Pesa for Business Account**
   - Visit Safaricom shop with documents
   - Get unique Till Number (e.g., 654321)
   - Activate and test with small transaction

2. **Developer Credentials**
   - Consumer Key: `ABC123xyz...`
   - Consumer Secret: `XYZ789abc...`
   - Passkey: `bfb279f9aa9bdbcf...`
   - Shortcode: Your till number

### Configure in Comolor POS
1. Login as Shop Admin
2. Settings → Payment Configuration
3. Enter your MPesa credentials
4. Test with small transaction
5. Activate for live use

## Important Till Numbers

- **Super Admin Till**: 0797237383 (for license payments)
- **Shop Till**: Each shop gets unique number from Safaricom

## Timeline Expectations

- **M-Pesa for Business**: 1-2 days (if documents ready)
- **Developer Account**: Immediate
- **Production App Approval**: 2-5 business days
- **Testing & Go-Live**: 1-2 days

## Emergency Contacts

- **Safaricom Business**: 0722 002 200
- **Developer Support**: developer@safaricom.co.ke
- **Comolor Support**: comolor07@gmail.com

## Cost Structure

- **Setup**: Free (except business registration costs)
- **Transaction Fees**: 1-2% charged by Safaricom
- **License Fee**: KSh 1,500/month to Super Admin till

## Security Reminders

- Never share credentials with unauthorized persons
- Use HTTPS for all production callbacks
- Regularly rotate API keys
- Monitor transaction logs daily
- Report suspicious activity immediately

## Testing Checklist

### Super Admin Testing
- [ ] License payment received
- [ ] Shop activation works
- [ ] Webhook callbacks functioning
- [ ] Audit logs created

### Shop Testing
- [ ] Customer payment received
- [ ] Transaction recorded in system
- [ ] Receipt generated
- [ ] Inventory updated
- [ ] SMS notifications sent

For detailed instructions, see:
- `mpesa_production_setup_guide.md`
- `system_mpesa_configuration_guide.md`