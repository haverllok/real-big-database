-- Reference answer — indexes worth adding for typical e-commerce query
-- patterns against this dataset. Don't peek until you've tried to find
-- these yourself with EXPLAIN / EXPLAIN ANALYZE.
--
-- Note for MySQL specifically: InnoDB automatically creates an index on
-- every FOREIGN KEY column (you can see them with SHOW INDEX), so those
-- are already covered here. The gaps below are everything InnoDB does
-- NOT give you for free.

CREATE UNIQUE INDEX idx_customers_email ON customers(email);
CREATE UNIQUE INDEX idx_products_sku    ON products(sku);
CREATE INDEX idx_orders_status          ON orders(status);
CREATE INDEX idx_orders_order_date      ON orders(order_date);

-- Composite index for a common report: "a customer's orders, newest first"
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date DESC);