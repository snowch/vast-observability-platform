-- Initialize PostgreSQL for monitoring

CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

CREATE USER monitor_user WITH PASSWORD 'monitor_password';

GRANT CONNECT ON DATABASE app_db TO monitor_user;
GRANT USAGE ON SCHEMA public TO monitor_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitor_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO monitor_user;
GRANT pg_monitor TO monitor_user;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    order_number VARCHAR(50) NOT NULL UNIQUE,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, email) VALUES
    ('john_doe', 'john@example.com'),
    ('jane_smith', 'jane@example.com'),
    ('bob_wilson', 'bob@example.com')
ON CONFLICT (username) DO NOTHING;

INSERT INTO products (name, description, price, stock_quantity) VALUES
    ('Laptop', 'High-performance laptop', 1299.99, 50),
    ('Mouse', 'Wireless mouse', 29.99, 200),
    ('Keyboard', 'Mechanical keyboard', 149.99, 100)
ON CONFLICT DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);

ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET pg_stat_statements.max = 10000;
