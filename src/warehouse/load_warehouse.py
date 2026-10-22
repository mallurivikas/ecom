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


def load_dim_customers(df):
    query = text("""
        INSERT INTO dim_customers (
            customer_id,
            first_name,
            last_name,
            email,
            country,
            created_at
        )
        VALUES (
            :customer_id,
            :first_name,
            :last_name,
            :email,
            :country,
            :created_at
        )
        ON CONFLICT (customer_id)
        DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            email = EXCLUDED.email,
            country = EXCLUDED.country,
            created_at = EXCLUDED.created_at
    """)

    records = df.to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(query, records)

    print(f"  Rows processed: {len(df)}")


def load_dim_products(df):
    query = text("""
        INSERT INTO dim_products (
            product_id,
            product_name,
            category,
            price,
            created_at
        )
        VALUES (
            :product_id,
            :product_name,
            :category,
            :price,
            :created_at
        )
        ON CONFLICT (product_id)
        DO UPDATE SET
            product_name = EXCLUDED.product_name,
            category = EXCLUDED.category,
            price = EXCLUDED.price,
            created_at = EXCLUDED.created_at
    """)

    records = df.to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(query, records)

    print(f"  Rows processed: {len(df)}")


def load_fact_orders(df):
    query = text("""
        INSERT INTO fact_orders (
            order_id,
            customer_id,
            order_date,
            status,
            total_amount,
            item_count,
            total_quantity
        )
        VALUES (
            :order_id,
            :customer_id,
            :order_date,
            :status,
            :total_amount,
            :item_count,
            :total_quantity
        )
        ON CONFLICT (order_id)
        DO UPDATE SET
            customer_id = EXCLUDED.customer_id,
            order_date = EXCLUDED.order_date,
            status = EXCLUDED.status,
            total_amount = EXCLUDED.total_amount,
            item_count = EXCLUDED.item_count,
            total_quantity = EXCLUDED.total_quantity
    """)

    records = df.to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(query, records)

    print(f"  Rows processed: {len(df)}")


def load_fact_order_items(df):
    query = text("""
        INSERT INTO fact_order_items (
            order_item_id,
            order_id,
            product_id,
            quantity,
            unit_price,
            item_total
        )
        VALUES (
            :order_item_id,
            :order_id,
            :product_id,
            :quantity,
            :unit_price,
            :item_total
        )
        ON CONFLICT (order_item_id)
        DO UPDATE SET
            order_id = EXCLUDED.order_id,
            product_id = EXCLUDED.product_id,
            quantity = EXCLUDED.quantity,
            unit_price = EXCLUDED.unit_price,
            item_total = EXCLUDED.item_total
    """)

    records = df.to_dict(orient="records")

    with engine.begin() as connection:
        connection.execute(query, records)

    print(f"  Rows processed: {len(df)}")


def load_table(table_name):
    input_file = GOLD_DIR / f"{table_name}.csv"

    print(f"Loading {table_name}...")
    print(f"  Source: {input_file}")

    df = pd.read_csv(input_file)

    print(f"  Rows read: {len(df)}")

    df = prepare_table(table_name, df)

    print("  Data types prepared:")
    print(df.dtypes)

    if table_name == "dim_customers":
        load_dim_customers(df)

    elif table_name == "dim_products":
        load_dim_products(df)

    elif table_name == "fact_orders":
        load_fact_orders(df)

    elif table_name == "fact_order_items":
        load_fact_order_items(df)

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