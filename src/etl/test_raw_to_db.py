from __future__ import annotations
import pandas as pd
import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from src.db.engine import get_engine
from src.etl.raw_to_db import RAW_DATA_DIRECTORY, load_all_raw


# Map DB tables to their sourc CSV filenames
TABLE_CSV_MAP = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "categories": "product_category_name_translation.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv"
}


def _truncate_raw_tables() -> None:
    """
    Truncate all raw tables so that ETL can be run idempotently on tests.

    WARNING: this is meant for local DBs only. It wipes data in these tables.
    """
    engine = get_engine()
    # TRUNCATE with CASCADE handles FK dependencies automatically
    raw_tables = (
        "reviews, payments, items, orders, products, sellers, categories, geolocation, customers"
    )
    with engine.begin() as conn:
        conn.execute(
            text(f"TRUNCATE TABLE {raw_tables} RESTART IDENTITY CASCADE;")
        )


def _count_rows_in_table(table_name: str) -> int:
    """
    Return number of rows in a given table.
    """
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar_one()
    

def test_raw_to_db_row_counts_match() -> None:
    """
    Smoke test for the CSV -> DB ETL.
    Checks that each table has the same number of rows as its source CSV.
    """
    engine = get_engine()
    # If DB not reachable, skip the test
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip("Database not available; make sure Docker container is running.")

    # 1. Clean tables
    _truncate_raw_tables()

    # 2. Run ETL
    load_all_raw(engine, RAW_DATA_DIRECTORY)

    # 3. Compare CSV row counts vs DB counts
    data_dir = RAW_DATA_DIRECTORY
    for table, filename in TABLE_CSV_MAP.items():
        csv_path = data_dir / filename
        assert csv_path.exists(), f"CSV not found for {table}: {csv_path}"

        csv_rows = len(pd.read_csv(csv_path))
        db_rows = _count_rows_in_table(table)

        assert (csv_rows == db_rows), f"Row mismatch for {table}: CSV={csv_rows} != DB={db_rows}"

