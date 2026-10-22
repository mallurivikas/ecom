from pathlib import Path

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = PROJECT_ROOT / "data" / "gold"

load_dotenv(PROJECT_ROOT / ".env")


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

WAREHOUSE_DB = "ecommerce_dw"

DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{WAREHOUSE_DB}"
)

engine = create_engine(DATABASE_URL)


TABLES = [
    "dim_customers",
    "dim_products",
    "fact_orders",
    "fact_order_items",
]


def prepare_table(table_name, df):
    if table_name == "dim_customers":
        df["customer_id"] = pd.to_numeric(
            df["customer_id"], errors="raise"
        )
        df["created_at"] = pd.to_datetime(
            df["created_at"], errors="raise"
        )

    elif table_name == "dim_products":
        df["product_id"] = pd.to_numeric(
            df["product_id"], errors="raise"
        )
        df["price"] = pd.to_numeric(
            df["price"], errors="raise"
        )
        df["created_at"] = pd.to_datetime(
            df["created_at"], errors="raise"
        )

    elif table_name == "fact_orders":
        df["order_id"] = pd.to_numeric(
            df["order_id"], errors="raise"
        )
        df["customer_id"] = pd.to_numeric(
            df["customer_id"], errors="raise"
        )
        df["order_date"] = pd.to_datetime(
            df["order_date"], errors="raise"
        )
        df["total_amount"] = pd.to_numeric(
            df["total_amount"], errors="raise"
        )
        df["item_count"] = pd.to_numeric(
            df["item_count"], errors="raise"
        )
        df["total_quantity"] = pd.to_numeric(
            df["total_quantity"], errors="raise"
        )

    elif table_name == "fact_order_items":
        df["order_item_id"] = pd.to_numeric(
            df["order_item_id"], errors="raise"
        )
        df["order_id"] = pd.to_numeric(
            df["order_id"], errors="raise"
        )
        df["product_id"] = pd.to_numeric(
            df["product_id"], errors="raise"
        )
        df["quantity"] = pd.to_numeric(
            df["quantity"], errors="raise"
        )
        df["unit_price"] = pd.to_numeric(
            df["unit_price"], errors="raise"
        )
        df["item_total"] = pd.to_numeric(
            df["item_total"], errors="raise"
        )

    return df


def load_table(table_name):
    input_file = GOLD_DIR / f"{table_name}.csv"

    print(f"Loading {table_name}...")
    print(f"  Source: {input_file}")

    df = pd.read_csv(input_file)

    print(f"  Rows read: {len(df)}")

    df = prepare_table(table_name, df)

    print("  Data types prepared:")
    print(df.dtypes)

    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
    )

    print(f"  Rows loaded: {len(df)}")
    print()


def verify_table(table_name):
    query = text(
        f"SELECT COUNT(*) FROM {table_name}"
    )

    with engine.connect() as connection:
        count = connection.execute(query).scalar()

    print(f"  {table_name}: {count} rows")


def main():
    print("=" * 60)
    print("STARTING GOLD → DATA WAREHOUSE LOAD")
    print("=" * 60)
    print()

    for table in TABLES:
        load_table(table)

    print("=" * 60)
    print("VERIFYING WAREHOUSE")
    print("=" * 60)
    print()

    for table in TABLES:
        verify_table(table)

    print()
    print("=" * 60)
    print("WAREHOUSE LOAD COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()