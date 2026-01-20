-- ---------------------
-- Base Olist Schema
-- ---------------------

-- customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT NOT NULL,
    customer_zip_code_prefix INTEGER NOT NULL,
    customer_city TEXT NOT NULL,
    customer_state CHAR(2) NOT NULL
);

-- geolocation (many duplicates)
CREATE TABLE IF NOT EXISTS geolocation (
    geolocation_id BIGSERIAL PRIMARY KEY,
    geolocation_zip_code_prefix INTEGER NOT NULL,
    geolocation_lat DOUBLE PRECISION NOT NULL,
    geolocation_lng DOUBLE PRECISION NOT NULL,
    geolocation_city TEXT NOT NULL,
    geolocation_state CHAR(2) NOT NULL
);

-- categories
CREATE TABLE IF NOT EXISTS categories (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
);

-- sellers
CREATE TABLE IF NOT EXISTS sellers (
    seller_id TEXT PRIMARY KEY,
    seller_zip_code_prefix INTEGER NOT NULL,
    seller_city TEXT NOT NULL,
    seller_state CHAR(2) NOT NULL
);

-- orders 
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_status TEXT NOT NULL,
    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date DATE NOT NULL,
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- items 
CREATE TABLE IF NOT EXISTS items (
    order_id TEXT NOT NULL,
    order_item_id SMALLINT NOT NULL,
    product_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    shipping_limit_date TIMESTAMP NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    freight_value NUMERIC(10,2) NOT NULL,
    CONSTRAINT pk_order_items PRIMARY KEY (order_id, order_item_id),
    CONSTRAINT fk_items_order 
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
    CONSTRAINT fk_items_sellers 
        FOREIGN KEY (seller_id) REFERENCES sellers(seller_id),
    CONSTRAINT fk_items_products 
        FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- products
CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_name_lenght INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty INTEGER,
    product_weight_g DOUBLE PRECISION,
    product_length_cm DOUBLE PRECISION,
    product_height_cm DOUBLE PRECISION,
    product_width_cm DOUBLE PRECISION,
    CONSTRAINT fk_products_category
        FOREIGN KEY (product_category_name) REFERENCES categories(product_category_name)
);

-- payments
CREATE TABLE IF NOT EXISTS payments (
    order_id TEXT NOT NULL,
    payment_sequential SMALLINT NOT NULL,
    payment_type TEXT NOT NULL,
    payment_installments SMALLINT NOT NULL,
    payment_value NUMERIC(10,2) NOT NULL,
    CONSTRAINT pk_order_payments PRIMARY KEY (order_id, payment_sequential),
    CONSTRAINT fk_payments_order 
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- reviews 
CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    review_score SMALLINT NOT NULL,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date DATE NOT NULL,
    review_answer_timestamp TIMESTAMP NOT NULL,
    CONSTRAINT pk_order_reviews PRIMARY KEY (order_id, review_id),
    CONSTRAINT fk_reviews_order 
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
);


-- -----------------------
-- Model Tracking Tables
-- -----------------------

CREATE TABLE IF NOT EXISTS model_runs (
    run_id SERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    run_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    params JSONB,
    metrics JSONB
);



-- ----------------
-- Helpful Indexes 
-- ----------------

-- time based queries on orders
CREATE INDEX IF NOT EXISTS idx_orders_purchase_ts
    ON orders (order_purchase_timestamp);

-- Joining by customer
CREATE INDEX IF NOT EXISTS idx_orders_customer_id
    ON orders (customer_id);

-- Joining by FK on items
CREATE INDEX IF NOT EXISTS idx_items_product_id
    ON items (product_id);

CREATE INDEX IF NOT EXISTS idx_items_seller_id
    ON items (seller_id);

-- Joining on ZIP prefix
CREATE INDEX IF NOT EXISTS idx_customers_zip_prefix
    ON customers (customer_zip_code_prefix);

CREATE INDEX IF NOT EXISTS idx_sellers_zip_prefix
    ON sellers (seller_zip_code_prefix);

CREATE INDEX IF NOT EXISTS idx_geolocation_zip_prefix
    ON geolocation (geolocation_zip_code_prefix);
