DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    city TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    product TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    ordered_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO customers (id, name, email, city) VALUES
(1, 'Alice Johnson', 'alice@example.com', 'New York'),
(2, 'Bob Smith', 'bob@example.com', 'Chicago'),
(3, 'Carol Davis', 'carol@example.com', 'San Francisco'),
(4, 'David Lee', 'david@example.com', 'Austin'),
(5, 'Emma Wilson', 'emma@example.com', 'Seattle');

INSERT INTO orders (id, customer_id, product, quantity, price, status, ordered_at) VALUES
(1,  1, 'Laptop',          1, 1299.99, 'shipped',   '2026-01-05 10:30:00'),
(2,  1, 'Mouse',            2,   29.99, 'delivered', '2026-01-05 10:30:00'),
(3,  2, 'Keyboard',         1,   89.99, 'delivered', '2026-01-12 14:15:00'),
(4,  3, 'Monitor',          2,  349.99, 'shipped',   '2026-01-20 09:00:00'),
(5,  2, 'USB-C Hub',        1,   49.99, 'delivered', '2026-02-01 11:45:00'),
(6,  4, 'Headphones',       1,  199.99, 'pending',   '2026-02-03 16:20:00'),
(7,  5, 'Webcam',           1,   79.99, 'shipped',   '2026-02-10 08:30:00'),
(8,  1, 'Laptop Stand',     1,   45.99, 'delivered', '2026-02-14 13:00:00'),
(9,  3, 'External SSD',     1,  129.99, 'delivered', '2026-02-18 10:10:00'),
(10, 4, 'Mouse Pad',        3,   12.99, 'delivered', '2026-02-20 15:30:00'),
(11, 5, 'Desk Lamp',        1,   39.99, 'shipped',   '2026-02-25 09:45:00'),
(12, 2, 'HDMI Cable',       2,   14.99, 'delivered', '2026-03-01 12:00:00'),
(13, 3, 'Laptop',           1, 1299.99, 'pending',   '2026-03-05 17:30:00'),
(14, 1, 'Wireless Charger', 1,   34.99, 'pending',   '2026-03-08 08:00:00'),
(15, 5, 'Keyboard',         1,   89.99, 'shipped',   '2026-03-10 14:20:00'),
(16, 4, 'Monitor',          1,  349.99, 'pending',   '2026-03-12 11:00:00');

CREATE USER readonly_user WITH PASSWORD 'postgres';
GRANT CONNECT ON DATABASE myapp TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
