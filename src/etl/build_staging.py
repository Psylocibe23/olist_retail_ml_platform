from __future__ import annotations
from pathlib import Path
from sqlalchemy.engine import Engine
from sqlalchemy import text
from src.db.engine import get_engine


#--------------------------
# Helpers
#--------------------------

def _log_build(table_name: str) -> None:
    print(f"[STAGING] built {table_name}")

#--------------------------
# Create staging tables
#--------------------------

def build_stg_customers(engine: Engine) -> None:
    """
    Builds the stg_customers table from raw customers.

    - Keeps the same grain: one row per customer_id
    - Adds a normalized city column (lowercase, no accents, cleaned chars)
    - Idempotent: DROP + CREATE when run
    """
    with engine.begin() as conn:
        # 1. Drop staging table if already exists
        conn.execute(text("DROP TABLE IF EXISTS stg_customers"))

        # 2. Create staging table from raw customers
        conn.execute(
            text(
                """
                CREATE TABLE stg_customers AS
                SELECT 
                    customer_id,
                    customer_unique_id,
                    customer_zip_code_prefix,
                    -- lowercase, remove accents, keep only letters/digits/spaces
                    trim(
                        regexp_replace(
                            regexp_replace(
                                unaccent(LOWER(customer_city)),
                                '[^a-z0-9]+',
                                ' ',
                                'g'
                            ),
                            '\\s+',
                            ' ',
                            'g'
                        )
                    ) AS customer_city_norm,
                    customer_state
                FROM customers;
                """
            )
        )

        _log_build("stg_customers")


def build_stg_geolocation(engine: Engine) -> None:
    """
    Builds the stg_geolocation table from raw geolocation.

    - Aggregate by (geolocation_zip_code_prefix, geolocation_city, geolocation_state)
    - Adds a normalized city column (lowercase, no accents, cleaned chars)
    - Idempotent: DROP + CREATE when run
    """
    with engine.begin() as conn:
        # 1. Drop staging table if already exists 
        conn.execute(text("DROP TABLE IF EXISTS stg_geolocation"))

        # 2. Create staging table from raw geolocation
        conn.execute(text(
            """
            CREATE TABLE stg_geolocation AS
            SELECT
                geolocation_zip_code_prefix AS zip_prefix,
                geolocation_state,
                trim(
                    regexp_replace(
                        regexp_replace(
                            unaccent(LOWER(geolocation_city)),
                            '[^a-z0-9]+',
                            ' ',
                            'g'
                        ),
                        '\\s+',
                        ' ',
                        'g'
                    )
                ) AS geolocation_city_norm,
                AVG(geolocation_lat) AS lat_mean,
                AVG(geolocation_lng) AS lng_mean,
                COUNT(*) AS n_points
            FROM geolocation
            GROUP BY
                zip_prefix,
                geolocation_state,
                geolocation_city_norm;
            """
        ))

        _log_build("stg_geolocation")


def build_stg_sellers(engine: Engine) -> None:
    """
    Builds the stg_sellers table from raw sellers.

    - Keeps the same grain: one row per seller_id
    - Adds a normalized city column (lowercase, no accents, cleaned chars)
    - Idempotent: DROP + CREATE when run 
    """
    with engine.begin() as conn:
        # 1. Drop staging table if already exists
        conn.execute(text("DROP TABLE IF EXISTS stg_sellers"))

        # 2. Create staging table from raw sellers
        conn.execute(text(
            """
            CREATE TABLE stg_sellers AS
            SELECT 
                seller_id,
                seller_zip_code_prefix,
                trim(
                    regexp_replace(
                        regexp_replace(
                            unaccent(LOWER(seller_city)),
                            '[^a-z0-9]+',
                            ' ',
                            'g'
                        ),
                        '\\s+',
                        ' ',
                        'g'
                    )
                ) AS seller_city_norm,
                seller_state
            FROM sellers;
            """
        ))

        _log_build("stg_sellers")


def build_stg_orders(engine: Engine) -> None:
    """
    Builds the stg_orders table from raw orders.

    - Keeps the same grain: one row per order_id
    - Creates flags 'delivered', 'canceled'
    - Adds order_date (DATE) for daily aggregations
    - Idempotent: DROP + CREATE when run 
    """
    with engine.begin() as conn:
        # 1. Drop staging table if already exists
        conn.execute(text("DROP TABLE IF EXISTS stg_orders"))

        # 2. Create staging table from raw orders
        conn.execute(text(
            """
            CREATE TABLE stg_orders AS
            SELECT 
                order_id,
                customer_id,
                order_status,
                order_purchase_timestamp,
                order_approved_at,
                order_delivered_carrier_date,
                order_delivered_customer_date,
                order_estimated_delivery_date,
                order_purchase_timestamp::date AS order_date,
                CASE 
                    WHEN order_status = 'delivered'
                    THEN TRUE
                    ELSE FALSE
                END AS is_delivered,
                CASE
                    WHEN order_status IN ('canceled', 'unavailable')
                    THEN TRUE
                    ELSE FALSE
                END AS is_canceled
            FROM orders;
            """
        ))

        _log_build("stg_orders")


def build_stg_items(engine: Engine) -> None:
    """
    Builds the stg_items table from raw items.

    - Grain: one row per (order_id, order_item_id)
    - Adds item_total = price + freight_value
    """
    with engine.begin() as conn:
        # 1. Drop staging table if already exists
        conn.execute(text("DROP TABLE IF EXISTS stg_items"))

        # 2. Create staging table from raw items
        conn.execute(text(
            """
            CREATE TABLE stg_items AS
            SELECT
                order_id,
                order_item_id,
                product_id,
                seller_id,
                shipping_limit_date,
                price,
                freight_value,
                (price + freight_value) AS item_total
            FROM items;
            """
        ))

        _log_build("stg_items")


def build_stg_products(engine: Engine) -> None:
    """
    Builds stg_products from raw products.

    - Grain: one row per product_id
    - Mostly a cleaned 1:1 mirror; category FK was already cleaned in raw load
    """
    with engine.begin() as conn:
        # 1. Drop staging table if already exists
        conn.execute(text("DROP TABLE IF EXISTS stg_products"))

        # 2. Create staging table from raw products
        conn.execute(text(
            """
            CREATE TABLE stg_products AS
            SELECT
                product_id,
                product_category_name,
                product_name_lenght,
                product_description_lenght,
                product_photos_qty,
                product_weight_g,
                product_length_cm,
                product_height_cm,
                product_width_cm
            FROM products;
            """
        ))

        _log_build("stg_products")


def build_stg_payments(engine: Engine) -> None:
    """
    Builds stg_payments from raw payments.

    - Grain: one row per (order_id, payment_sequential)
    - Adds is_first_payment flag
    """
    with engine.begin() as conn:
        # 1. Drop staging table if already exists
        conn.execute(text("DROP TABLE IF EXISTS stg_payments"))

        # 2. Create staging table from raw payments
        conn.execute(text(
            """
            CREATE TABLE stg_payments AS
            SELECT
                order_id,
                payment_sequential,
                payment_type,
                payment_installments,
                payment_value,
                CASE
                    WHEN payment_sequential = 1
                    THEN TRUE
                    ELSE FALSE
                END AS is_first_payment
            FROM payments;
            """
        ))

        _log_build("stg_payments")


def build_stg_reviews(engine: Engine) -> None:
    """
    Builds stg_reviews from raw reviews.

    - Grain: one row per (order_id, review_id)
    - Adds has_comment flag for convenience
    """
    with engine.begin() as conn:
        # 1. Drop staging table if already exists
        conn.execute(text("DROP TABLE IF EXISTS stg_reviews"))

        # 2. Create staging table from raw reviews
        conn.execute(text(
            """
            CREATE TABLE stg_reviews AS
            SELECT
                review_id,
                order_id,
                review_score,
                review_comment_title,
                review_comment_message,
                review_creation_date,
                review_answer_timestamp,
                (review_comment_message IS NOT NULL) AS has_comment
            FROM reviews;
            """
        ))

        _log_build("stg_reviews")


def build_stg_categories(engine: Engine) -> None:
    """
    Simple mirror of categories as a small reference dimension.
    """
    with engine.begin() as conn:
        # 1. Drop staging table if already exists
        conn.execute(text("DROP TABLE IF EXISTS stg_categories"))

        # 2. Create staging table from raw categories
        conn.execute(text(
            """
            CREATE TABLE stg_categories AS
            SELECT
                product_category_name,
                product_category_name_english
            FROM categories;
            """
        ))

        _log_build("stg_categories")

#--------------------------
# Main  
#--------------------------

def main():
    engine = get_engine()
    build_stg_customers(engine)
    build_stg_geolocation(engine)
    build_stg_sellers(engine)
    build_stg_orders(engine)
    build_stg_items(engine)
    build_stg_products(engine)
    build_stg_payments(engine)
    build_stg_reviews(engine)
    build_stg_categories(engine)

if __name__ == "__main__":
    main()
