-- Reference answer — indexes worth adding for typical e-commerce query
-- patterns against this dataset. Don't peek until you've tried to find
-- these yourself with EXPLAIN ANALYZE.
--
-- Note for PostgreSQL specifically: unlike MySQL/InnoDB, Postgres does
-- NOT automatically index a column just because it carries a FOREIGN KEY.
-- Every FK column below is a genuine missing index out of the box.

-- FK columns used constantly in JOINs
CREATE INDEX idx_products_category_id   ON products(category_id);
CREATE INDEX idx_products_supplier_id   ON products(supplier_id);
CREATE INDEX idx_addresses_customer_id  ON addresses(customer_id);
CREATE INDEX idx_orders_customer_id     ON orders(customer_id);
CREATE INDEX idx_orders_address_id      ON orders(address_id);
CREATE INDEX idx_order_items_order_id   ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_payments_order_id      ON payments(order_id);
CREATE INDEX idx_shipments_order_id     ON shipments(order_id);
CREATE INDEX idx_reviews_product_id     ON reviews(product_id);
CREATE INDEX idx_reviews_customer_id    ON reviews(customer_id);

-- Frequent filter/sort columns
CREATE UNIQUE INDEX idx_customers_email ON customers(email);
CREATE UNIQUE INDEX idx_products_sku    ON products(sku);
CREATE INDEX idx_orders_status          ON orders(status);
CREATE INDEX idx_orders_order_date      ON orders(order_date);

-- Composite index for a common report: "a customer's orders, newest first"
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date DESC);