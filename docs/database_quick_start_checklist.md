# Multi-Tenant Database Quick Start Checklist

## Pre-Deployment Checklist

### Server Requirements
- [ ] Ubuntu 20.04+ or Debian 11+ server
- [ ] Minimum 2GB RAM (4GB+ recommended)
- [ ] 20GB+ storage space
- [ ] Root or sudo access
- [ ] Domain name configured (optional but recommended)

### Database Setup (30 minutes)

**1. Install PostgreSQL**
```bash
apt update && apt upgrade -y
apt install postgresql postgresql-contrib -y
systemctl start postgresql && systemctl enable postgresql
```

**2. Create Production Database**
```bash
sudo -u postgres psql
CREATE DATABASE comolor_pos_production;
CREATE USER comolor_app WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE comolor_pos_production TO comolor_app;
```

**3. Run Schema Setup**
- Download `setup_database.sql` from deployment guide
- Run: `sudo -u postgres psql -f setup_database.sql`

**4. Configure PostgreSQL**
- Edit `/etc/postgresql/14/main/postgresql.conf`
- Set memory settings based on server RAM
- Restart: `systemctl restart postgresql`

### Security Setup (15 minutes)

**5. Firewall Configuration**
```bash
ufw default deny incoming
ufw allow ssh && ufw allow 80 && ufw allow 443
ufw enable
```

**6. Database Security**
- Change default passwords immediately
- Restrict database access to localhost only
- Create read-only user for reporting

### Application Deployment (20 minutes)

**7. Environment Configuration**
```bash
# Create production environment file
DATABASE_URL=postgresql://comolor_app:password@localhost/comolor_pos_production
SECRET_KEY=your_super_secure_secret_key
MPESA_ENVIRONMENT=production
```

**8. Run Migration Script**
```bash
export DATABASE_URL="your_database_url"
python3 migrate_to_production.py
```

### Testing and Verification (10 minutes)

**9. Test Database Connection**
- Verify application connects successfully
- Check all tables created properly
- Test super admin login (admin/admin123)
- Test demo shop functionality

**10. Performance Check**
```sql
-- Verify indexes exist
\d+ products
\d+ sales
-- Check tenant isolation
SELECT shop_id, count(*) FROM products GROUP BY shop_id;
```

## Post-Deployment Tasks

### Immediate (First Day)
- [ ] Change all default passwords
- [ ] Test MPesa integration with small transaction
- [ ] Set up automated backups
- [ ] Configure monitoring alerts
- [ ] Test disaster recovery procedure

### Within First Week
- [ ] Monitor query performance
- [ ] Optimize slow queries if any
- [ ] Set up SSL certificates
- [ ] Configure log rotation
- [ ] Train initial users

### Ongoing Maintenance
- [ ] Weekly backup verification
- [ ] Monthly performance review
- [ ] Quarterly security audit
- [ ] Update database statistics
- [ ] Monitor disk usage

## Common Issues and Solutions

**Connection Refused**
- Check PostgreSQL is running: `systemctl status postgresql`
- Verify firewall settings: `ufw status`
- Check pg_hba.conf authentication

**Slow Performance**
- Verify indexes exist: `\d+ table_name`
- Check memory settings in postgresql.conf
- Monitor with: `SELECT * FROM pg_stat_activity;`

**Out of Disk Space**
- Clean old log files: `find /var/log -name "*.log" -mtime +7 -delete`
- Vacuum database: `VACUUM ANALYZE;`
- Rotate backups: Remove old backup files

**Permission Errors**
- Check user privileges: `\dp` in psql
- Verify ownership: `\l` to list databases
- Grant missing permissions as needed

## Emergency Contacts

- **Database Issues**: Check logs in `/var/log/postgresql/`
- **Application Issues**: Check application logs
- **Security Issues**: Immediately revoke affected credentials
- **Backup Issues**: Verify backup files and test restore

## Success Metrics

**Day 1**
- Database responding to queries
- All shops can access their data only
- No cross-tenant data leakage
- Backup system functioning

**Week 1**
- Query response times <100ms for typical operations
- No unauthorized access attempts
- All shops successfully onboarded
- Performance metrics within expected ranges

**Month 1**
- Zero data loss incidents
- 99.9%+ uptime
- Backup and recovery tested successfully
- Performance optimization complete

## Scaling Indicators

**Consider Read Replicas When:**
- Average query response time >200ms
- CPU usage consistently >70%
- Multiple complex reporting queries

**Consider Partitioning When:**
- Sales table >1 million records per shop
- Query performance degrading
- Backup times >30 minutes

**Consider Separate Databases When:**
- Enterprise customers requiring isolation
- Compliance requirements mandate separation
- Performance requirements exceed shared infrastructure

## Next Steps After Deployment

1. **User Training**: Train shop owners on system usage
2. **Documentation**: Create user guides specific to your deployment
3. **Monitoring**: Set up automated monitoring and alerting
4. **Optimization**: Fine-tune based on actual usage patterns
5. **Scaling**: Plan for growth and additional features

This checklist ensures a successful multi-tenant database deployment for the Comolor POS system.