from __future__ import annotations
from pathlib import Path
from sqlalchemy.engine import Engine
from sqlalchemy import text
from src.db.engine import get_engine
from src.etl.raw_to_db import RAW_DATA_DIRECTORY, load_all_raw


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
                    customer_city,
                    -- lowercase, remove accents, keep only letters/digits/spaces
                    trim(
                        regexp_replace(
                            unaccent(LOWER(customer_city)),
                            '[^a-z0-9]+',
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


#--------------------------
# Main  
#--------------------------

def main():
    engine = get_engine()
    build_stg_customers(engine)

if __name__ == "__main__":
    main()