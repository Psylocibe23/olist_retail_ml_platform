from __future__ import annotations
from sqlalchemy import text
from sqlalchemy.engine import Engine
from src.db.engine import get_engine


#--------------------------
# Helpers
#--------------------------

def _log_build(table_name: str) -> None:
    print(f"[MART] built {table_name}")


# --------------------------
# Fact tables
# --------------------------

def build_fact_orders(engine: Engine) -> None:
    """
    Build fact_orders from staging tables.

    Grain: one row per order_id.

    Joins:
    - stg_orders (base order info, dates, flags)
    - stg_items -> aggregates: n_items, revenue, freight, gross order value
    - stg_payments -> aggregates: total paid, max installments, first payment type
    - stg_reviews -> aggregates: avg review_score and has_comment flag

    Also computes a couple of time deltas in days.
    """
    with engine.begin() as conn:
        # 1. Drop if exists so the build is idempotent
        conn.execute(text("DROP TABLE IF EXISTS fact_orders"))

        # 2. Build fact table from staging tables
        conn.execute(text(
            """
            CREATE TABLE fact_orders AS
            SELECT
                o.order_id,
                o.customer_id,
                o.order_date,
                o.order_status,
                o.is_delivered,
                o.is_canceled,
                o.order_purchase_timestamp,
                o.order_delivered_customer_date,
                o.order_estimated_delivery_date,

                CASE 
                    WHEN o.order_delivered_customer_date IS NOT NULL
                    THEN (o.order_delivered_customer_date::date - o.order_purchase_timestamp::date)
                    ELSE NULL
                END AS delivery_time_days,

                CASE 
                    WHEN o.order_delivered_customer_date IS NOT NULL
                    THEN (o.order_delivered_customer_date::date - o.order_estimated_delivery_date::date)
                    ELSE NULL
                END AS delay_vs_estimated_days,

                -- items aggregation
                COALESCE(i.n_items, 0) AS n_items,
                COALESCE(i.items_price_sum, 0) AS items_price_sum,
                COALESCE(i.freight_sum, 0) AS freight_sum,
                COALESCE(i.order_gross_value, 0) AS order_gross_value,

                -- payments aggregation
                p.payment_value_total,
                p.payment_installments_max,
                p.first_payment_type,

                -- review aggregation
                r.review_score_avg,
                r.has_comment

            FROM stg_orders AS o

            LEFT JOIN (
                SELECT
                    order_id,
                    COUNT(*) AS n_items,
                    SUM(price) AS items_price_sum,
                    SUM(freight_value) AS freight_sum,
                    SUM(item_total) AS order_gross_value
                FROM stg_items
                GROUP BY order_id
            ) AS i
              ON i.order_id = o.order_id

            LEFT JOIN (
                SELECT
                    order_id,
                    SUM(payment_value) AS payment_value_total,
                    MAX(payment_installments) AS payment_installments_max,
                    MAX(
                        CASE
                            WHEN is_first_payment THEN payment_type
                            ELSE NULL
                        END
                    ) AS first_payment_type
                FROM stg_payments
                GROUP BY order_id
            ) AS p
              ON p.order_id = o.order_id

            LEFT JOIN (
                SELECT
                    order_id,
                    AVG(review_score)::NUMERIC(5,2) AS review_score_avg,
                    BOOL_OR(has_comment) AS has_comment
                FROM stg_reviews
                GROUP BY order_id
            ) AS r
              ON r.order_id = o.order_id;
            """
        ))

        # 3. Add primary key on order_id for faster joins
        conn.execute(text("ALTER TABLE fact_orders ADD PRIMARY KEY (order_id);"))

    _log_build("fact_orders")


def build_fact_daily_orders(engine: Engine) -> None:
    """
    Build fact_daily_orders from fact_orders.

    Grain: one row per order_date.

    Only non-canceled orders contribute to the main sales metrics
    (n_orders, revenue, etc.).
    """
    with engine.begin() as conn:
        # Rebuild idempotently
        conn.execute(text("DROP TABLE IF EXISTS fact_daily_orders"))

        conn.execute(text(
            """
            CREATE TABLE fact_daily_orders AS
            SELECT
                order_date,

                -- Only include non-canceled orders in main sales metrics
                COUNT(*) FILTER (WHERE NOT is_canceled) AS n_orders,
                SUM(order_gross_value) FILTER (WHERE NOT is_canceled) AS gross_revenue,
                SUM(items_price_sum) FILTER (WHERE NOT is_canceled) AS items_revenue,
                SUM(freight_sum) FILTER (WHERE NOT is_canceled) AS freight_revenue,
                AVG(order_gross_value) FILTER (WHERE NOT is_canceled) AS avg_order_value,
                SUM(n_items) FILTER (WHERE NOT is_canceled) AS n_items,

                -- Reviews: include any order that has a review_score_avg
                AVG(review_score_avg) AS avg_review_score,
                COUNT(review_score_avg) AS n_reviewed_orders,
                SUM(
                    CASE WHEN has_comment THEN 1 ELSE 0 END
                ) AS n_commented_reviews

            FROM fact_orders
            GROUP BY order_date;
            """
        ))

        conn.execute(text("ALTER TABLE fact_daily_orders ADD PRIMARY KEY (order_date);"))

    _log_build("fact_daily_orders")


def build_dim_date(engine: Engine) -> None:
    """
    Build dim_date (date/calendar dimension).

    Grain: one row per calendar date between the min and max order_date
    found in fact_daily_orders.

    Includes:
    - year, month, day
    - ISO day of week (1=Mon,...,7=Sun)
    - week of year
    - month name, short day name
    - is_weekend flag
    """
    with engine.begin() as conn:
        # Rebuild idempotently
        conn.execute(text("DROP TABLE IF EXISTS dim_date"))

        conn.execute(text(
            """
            CREATE TABLE dim_date AS
                WITH bounds AS (
                SELECT
                    MIN(order_date) AS min_date,
                    MAX(order_date) AS max_date
                FROM fact_daily_orders
                ),

                calendar AS (
                    SELECT
                        generate_series(min_date, max_date, interval '1 day')::date AS date
                    FROM bounds
                )

                SELECT
                    date,
                    EXTRACT(year FROM date)::int AS year,
                    EXTRACT(month FROM date)::int AS month,
                    EXTRACT(day FROM date)::int AS day,
                    EXTRACT(isodow FROM date)::int AS day_of_week_iso,
                    TO_CHAR(date, 'Dy') AS day_name_short,
                    TO_CHAR(date, 'Month') AS month_name,
                    EXTRACT(week FROM date)::int AS week_of_year,
                    (EXTRACT(isodow FROM date) IN (6,7)) AS is_weekend
                FROM calendar;
            """
        ))

        conn.execute(text("ALTER TABLE dim_date ADD PRIMARY KEY (date);"))

    _log_build("dim_date")

#--------------------------
# Main  
#--------------------------

def main():
    engine = get_engine()
    build_fact_orders(engine)
    build_fact_daily_orders(engine)
    build_dim_date(engine)

if __name__ == "__main__":
    main()
