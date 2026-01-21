from __future__ import annotations
import pandas as pd
from pathlib import Path
from sqlalchemy.engine import Engine
from sqlalchemy import text
from src.db.engine import get_engine


#--------------------------
# Paths
#--------------------------

# parents[0]=etl, [1]=db, [2]=project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIRECTORY = PROJECT_ROOT / "data" / "raw"


#--------------------------
# Helpers
#--------------------------

def _log_loaded(table: str, df: pd.DataFrame) -> None:
    print(f"Load {table}: inserted {len(df):,} rows")


#--------------------------
# Loaders for base tables
#--------------------------

def load_customers(engine: Engine, data_dir: Path = RAW_DATA_DIRECTORY) -> None:
    """
    Loads olist_customers_dataset.csv -> customers table.
    """
    csv_path = data_dir / "olist_customers_dataset.csv"
    df = pd.read_csv(csv_path)
    df.to_sql("customers", engine, if_exists="append", index=False, method="multi")
    _log_loaded("customers", df)


def load_geolocation(engine: Engine, data_dir: Path = RAW_DATA_DIRECTORY) -> None:
    """
    Loads olist_geolocation_dataset.csv -> geolocation table.
    """
    csv_path = data_dir / "olist_geolocation_dataset.csv"
    df = pd.read_csv(csv_path)
    df.to_sql("geolocation", engine, if_exists="append", index=False, method="multi", chunksize=10_000)
    _log_loaded("geolocation", df)


def load_items(engine: Engine, data_dir: Path = RAW_DATA_DIRECTORY) -> None:
    """
    Loads olist_order_items_dataset.csv -> items table.
    """
    csv_path = data_dir / "olist_order_items_dataset.csv"
    df = pd.read_csv(csv_path, parse_dates=["shipping_limit_date"])
    df.to_sql("items", engine, if_exists="append", index=False, method="multi")
    _log_loaded("items", df)


def load_payments(engine: Engine, data_dir: Path = RAW_DATA_DIRECTORY) -> None:
    """
    Loads olist_order_payments_dataset.csv -> payments table.
    """
    csv_path = data_dir / "olist_order_payments_dataset.csv"
    df = pd.read_csv(csv_path)
    df.to_sql("payments", engine, if_exists="append", index=False, method="multi")
    _log_loaded("payments", df)


def load_reviews(engine: Engine, data_dir: Path = RAW_DATA_DIRECTORY) -> None:
    """
    Loads olist_order_reviews_dataset.csv -> reviews table.
    """
    csv_path = data_dir / "olist_order_reviews_dataset.csv"
    df = pd.read_csv(csv_path, parse_dates=["review_creation_date", "review_answer_timestamp"])

    # review_creation_date is DATE in SQL schema
    df["review_creation_date"] = df["review_creation_date"].dt.date

    df.to_sql("reviews", engine, if_exists="append", index=False, method="multi")
    _log_loaded("reviews", df)


def load_orders(engine: Engine, data_dir: Path = RAW_DATA_DIRECTORY) -> None:
    """
    Loads olist_orders_dataset.csv -> orders table.
    """
    csv_path = data_dir / "olist_orders_dataset.csv"
    df = pd.read_csv(csv_path, parse_dates=["order_purchase_timestamp", 
                                            "order_approved_at", 
                                            "order_delivered_carrier_date", 
                                            "order_delivered_customer_date", 
                                            "order_estimated_delivery_date"])

    # order_estimated_delivery_date is DATE in SQL schema
    df["order_estimated_delivery_date"] = df["order_estimated_delivery_date"].dt.date

    df.to_sql("orders", engine, if_exists="append", index=False, method="multi")
    _log_loaded("orders", df)


def load_products(engine: Engine, data_dir: Path = RAW_DATA_DIRECTORY) -> None:
    """
    Loads olits_products_dataset.csv -> products table.
    Ensures that product_category_name values respect the FK to categories (2 missing category names in products table).
    """
    csv_path = data_dir / "olist_products_dataset.csv"
    df = pd.read_csv(csv_path)

    # Get list of valid product category names
    with engine.connect() as conn:
        result = conn.execute(text("SELECT product_category_name FROM categories"))
        valid_categories = {row[0] for row in result}  # Set of category names
    
    # For products with category names not present in categories set product_category_name to NULL
    mask_invalid = ~df["product_category_name"].isin(valid_categories) & df["product_category_name"].notna()
    n_invalid = int(mask_invalid.sum())
    if n_invalid > 0:
        print(f"[WARN] {n_invalid} products with unmapped category; setting product_category_name to NULL")
        df.loc[mask_invalid, "product_category_name"] = None


    df.to_sql("products", engine, if_exists="append", index=False, method="multi")
    _log_loaded("products", df)


def load_sellers(engine: Engine, data_dir: Path = RAW_DATA_DIRECTORY) -> None:
    """
    Loads olist_sellers_dataset.csv -> sellers table.
    """
    csv_path = data_dir / "olist_sellers_dataset.csv"
    df = pd.read_csv(csv_path)
    df.to_sql("sellers", engine, if_exists="append", index=False, method="multi")
    _log_loaded("sellers", df)


def load_categories(engine: Engine, data_dir: Path = RAW_DATA_DIRECTORY) -> None:
    """
    Load product_category_name_translation.csv -> categories table.
    """
    csv_path = data_dir / "product_category_name_translation.csv"
    df = pd.read_csv(csv_path)
    df.to_sql("categories", engine, if_exists="append", index=False, method="multi")
    _log_loaded("categories", df)


#--------------------------
# Orchestrator
#--------------------------

def load_all_raw(engine: Engine, data_dir: Path = RAW_DATA_DIRECTORY) -> None:
    """
    Run the whole raw csv -> DB load in a sensible dependency order.
    """
    # Tables without foreign keys
    load_customers(engine, data_dir)
    load_geolocation(engine, data_dir)
    load_categories(engine, data_dir)
    load_sellers(engine, data_dir)

    # Tables with references
    load_products(engine, data_dir)
    load_orders(engine, data_dir)
    load_items(engine, data_dir)
    load_payments(engine, data_dir)
    load_reviews(engine, data_dir)

    print("[LOAD] All raw tables loaded")


#--------------------------
# Main
#--------------------------

def main():
    engine = get_engine()
    load_all_raw(engine)

if __name__ == "__main__":
    main()