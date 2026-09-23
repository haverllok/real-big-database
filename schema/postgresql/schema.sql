-- Real Big Database — PostgreSQL schema
-- Foreign keys are present for referential integrity, but the dump
-- intentionally ships WITHOUT extra indexes beyond PRIMARY KEY / what a
-- FOREIGN KEY strictly requires. Query on this as-is, feel the pain on
-- large tables, then design your own indexing strategy.
-- See schema/postgresql/indexes_solution.sql for a reference answer.

DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS shipments CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS coupons CASCADE;
DROP TABLE IF EXISTS addresses CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

CREATE TABLE categories (
    id          INTEGER PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    parent_id   INTEGER REFERENCES categories(id),
    slug        VARCHAR(120) NOT NULL,
    created_at  TIMESTAMP NOT NULL
);

CREATE TABLE suppliers (
    id             INTEGER PRIMARY KEY,
    name           VARCHAR(150) NOT NULL,
    country        VARCHAR(60) NOT NULL,
    contact_email  VARCHAR(150) NOT NULL,
    created_at     TIMESTAMP NOT NULL
);

CREATE TABLE products (
    id            INTEGER PRIMARY KEY,
    sku           VARCHAR(32) NOT NULL,
    name          VARCHAR(200) NOT NULL,
    description   TEXT NOT NULL,
    category_id   INTEGER NOT NULL REFERENCES categories(id),
    supplier_id   INTEGER NOT NULL REFERENCES suppliers(id),
    price         DECIMAL(10,2) NOT NULL,
    weight_kg     DECIMAL(6,3) NOT NULL,
    is_active     BOOLEAN NOT NULL,
    attributes    JSONB NOT NULL,
    created_at    TIMESTAMP NOT NULL
);

CREATE TABLE customers (
    id          INTEGER PRIMARY KEY,
    first_name  VARCHAR(60) NOT NULL,
    last_name   VARCHAR(60) NOT NULL,
    email       VARCHAR(150) NOT NULL,
    phone       VARCHAR(30) NOT NULL,
    is_active   BOOLEAN NOT NULL,
    created_at  TIMESTAMP NOT NULL
);

CREATE TABLE addresses (
    id           INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    line1        VARCHAR(200) NOT NULL,
    line2        VARCHAR(200),
    city         VARCHAR(100) NOT NULL,
    state        VARCHAR(100) NOT NULL,
    postal_code  VARCHAR(20) NOT NULL,
    country      VARCHAR(60) NOT NULL,
    is_default   BOOLEAN NOT NULL
);

CREATE TABLE coupons (
    id                INTEGER PRIMARY KEY,
    code              VARCHAR(30) NOT NULL,
    discount_percent  DECIMAL(5,2) NOT NULL,
    valid_from        DATE NOT NULL,
    valid_to          DATE NOT NULL,
    max_uses          INTEGER NOT NULL,
    times_used        INTEGER NOT NULL
);

CREATE TABLE orders (
    id            INTEGER PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customers(id),
    address_id    INTEGER NOT NULL REFERENCES addresses(id),
    status        VARCHAR(20) NOT NULL,
    order_date    TIMESTAMP NOT NULL,
    total_amount  DECIMAL(12,2) NOT NULL,
    created_at    TIMESTAMP NOT NULL
);

CREATE TABLE order_items (
    id                INTEGER PRIMARY KEY,
    order_id          INTEGER NOT NULL REFERENCES orders(id),
    product_id        INTEGER NOT NULL REFERENCES products(id),
    quantity          INTEGER NOT NULL,
    unit_price        DECIMAL(10,2) NOT NULL,
    discount_amount   DECIMAL(10,2) NOT NULL
);

CREATE TABLE payments (
    id              INTEGER PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(id),
    payment_method  VARCHAR(20) NOT NULL,
    amount          DECIMAL(12,2) NOT NULL,
    status          VARCHAR(20) NOT NULL,
    paid_at         TIMESTAMP NOT NULL
);

CREATE TABLE shipments (
    id               INTEGER PRIMARY KEY,
    order_id         INTEGER NOT NULL REFERENCES orders(id),
    carrier          VARCHAR(50) NOT NULL,
    tracking_number  VARCHAR(50) NOT NULL,
    status           VARCHAR(20) NOT NULL,
    shipped_at       TIMESTAMP,
    delivered_at     TIMESTAMP
);

CREATE TABLE reviews (
    id           INTEGER PRIMARY KEY,
    product_id   INTEGER NOT NULL REFERENCES products(id),
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    rating       SMALLINT NOT NULL,
    title        VARCHAR(150) NOT NULL,
    body         TEXT NOT NULL,
    created_at   TIMESTAMP NOT NULL
);