-- Real Big Database — MySQL schema
-- Foreign keys are present for referential integrity, but the dump
-- intentionally ships WITHOUT extra indexes beyond PRIMARY KEY / what a
-- FOREIGN KEY strictly requires (InnoDB auto-creates an index on each
-- FK column, that's unavoidable — but there are no covering/composite
-- indexes here). Query on this as-is, feel the pain on large tables,
-- then design your own indexing strategy.
-- See schema/mysql/indexes_solution.sql for a reference answer.

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS coupons;
DROP TABLE IF EXISTS addresses;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS categories;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE categories (
    id          INT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    parent_id   INT,
    slug        VARCHAR(120) NOT NULL,
    created_at  DATETIME NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
) ENGINE=InnoDB;

CREATE TABLE suppliers (
    id             INT PRIMARY KEY,
    name           VARCHAR(150) NOT NULL,
    country        VARCHAR(60) NOT NULL,
    contact_email  VARCHAR(150) NOT NULL,
    created_at     DATETIME NOT NULL
) ENGINE=InnoDB;

CREATE TABLE products (
    id            INT PRIMARY KEY,
    sku           VARCHAR(32) NOT NULL,
    name          VARCHAR(200) NOT NULL,
    description   TEXT NOT NULL,
    category_id   INT NOT NULL,
    supplier_id   INT NOT NULL,
    price         DECIMAL(10,2) NOT NULL,
    weight_kg     DECIMAL(6,3) NOT NULL,
    is_active     BOOLEAN NOT NULL,
    attributes    JSON NOT NULL,
    created_at    DATETIME NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
) ENGINE=InnoDB;

CREATE TABLE customers (
    id          INT PRIMARY KEY,
    first_name  VARCHAR(60) NOT NULL,
    last_name   VARCHAR(60) NOT NULL,
    email       VARCHAR(150) NOT NULL,
    phone       VARCHAR(30) NOT NULL,
    is_active   BOOLEAN NOT NULL,
    created_at  DATETIME NOT NULL
) ENGINE=InnoDB;

CREATE TABLE addresses (
    id           INT PRIMARY KEY,
    customer_id  INT NOT NULL,
    line1        VARCHAR(200) NOT NULL,
    line2        VARCHAR(200),
    city         VARCHAR(100) NOT NULL,
    state        VARCHAR(100) NOT NULL,
    postal_code  VARCHAR(20) NOT NULL,
    country      VARCHAR(60) NOT NULL,
    is_default   BOOLEAN NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
) ENGINE=InnoDB;

CREATE TABLE coupons (
    id                INT PRIMARY KEY,
    code              VARCHAR(30) NOT NULL,
    discount_percent  DECIMAL(5,2) NOT NULL,
    valid_from        DATE NOT NULL,
    valid_to          DATE NOT NULL,
    max_uses          INT NOT NULL,
    times_used        INT NOT NULL
) ENGINE=InnoDB;

CREATE TABLE orders (
    id            INT PRIMARY KEY,
    customer_id   INT NOT NULL,
    address_id    INT NOT NULL,
    status        VARCHAR(20) NOT NULL,
    order_date    DATETIME NOT NULL,
    total_amount  DECIMAL(12,2) NOT NULL,
    created_at    DATETIME NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (address_id) REFERENCES addresses(id)
) ENGINE=InnoDB;

CREATE TABLE order_items (
    id                INT PRIMARY KEY,
    order_id          INT NOT NULL,
    product_id        INT NOT NULL,
    quantity          INT NOT NULL,
    unit_price        DECIMAL(10,2) NOT NULL,
    discount_amount   DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

CREATE TABLE payments (
    id              INT PRIMARY KEY,
    order_id        INT NOT NULL,
    payment_method  VARCHAR(20) NOT NULL,
    amount          DECIMAL(12,2) NOT NULL,
    status          VARCHAR(20) NOT NULL,
    paid_at         DATETIME NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
) ENGINE=InnoDB;

CREATE TABLE shipments (
    id               INT PRIMARY KEY,
    order_id         INT NOT NULL,
    carrier          VARCHAR(50) NOT NULL,
    tracking_number  VARCHAR(50) NOT NULL,
    status           VARCHAR(20) NOT NULL,
    shipped_at       DATETIME,
    delivered_at     DATETIME,
    FOREIGN KEY (order_id) REFERENCES orders(id)
) ENGINE=InnoDB;

CREATE TABLE reviews (
    id           INT PRIMARY KEY,
    product_id   INT NOT NULL,
    customer_id  INT NOT NULL,
    rating       SMALLINT NOT NULL,
    title        VARCHAR(150) NOT NULL,
    body         TEXT NOT NULL,
    created_at   DATETIME NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
) ENGINE=InnoDB;