-- Production PostgreSQL Database Setup for Comolor POS
-- Run this script on your production database server

-- Create database
CREATE DATABASE comolor_pos_production;

-- Connect to the database
\c comolor_pos_production;

-- Create extensions for better performance
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for multitenant queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_shop_id ON products(shop_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_shop_id ON sales(shop_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_shop_id ON users(shop_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_categories_shop_id ON categories(shop_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mpesa_transactions_shop_id ON mpesa_transactions(shop_id);

-- Create indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sales_created_at ON sales(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mpesa_transactions_transaction_id ON mpesa_transactions(transaction_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_shops_till_number ON shops(till_number);

-- Create backup user
CREATE USER backup_user WITH PASSWORD 'secure_backup_password';
GRANT CONNECT ON DATABASE comolor_pos_production TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_user;

-- Create monitoring user
CREATE USER monitor_user WITH PASSWORD 'secure_monitor_password';
GRANT CONNECT ON DATABASE comolor_pos_production TO monitor_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitor_user;

-- Set up connection limits
ALTER DATABASE comolor_pos_production SET max_connections = 100;

-- Configure for production
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_min_duration_statement = 1000;