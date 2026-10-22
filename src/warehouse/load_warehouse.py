import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_NAME = "ecommerce_dw"

DB_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DB_URL)

GOLD_DIR = Path("data/gold")

def get_watermark(pipeline_name):
    query = text("""
        SELECT last_watermark
        FROM pipeline_metadata
        WHERE pipeline_name = :pipeline_name
    """)

    with engine.connect() as connection:
        return connection.execute(
            query,
            {"pipeline_name": pipeline_name}
        ).scalar()


def update_watermark(pipeline_name, new_watermark):
    query = text("""
        UPDATE pipeline_metadata
        SET last_watermark = :new_watermark
        WHERE pipeline_name = :pipeline_name
    """)

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "pipeline_name": pipeline_name,
                "new_watermark": new_watermark
            }
        )


def prepare_table(df, table_name):
    if table_name == "dim_customers":
        df["customer_id"] = pd.to_numeric(
            df["customer_id"], errors="raise"
        ).astype("int64")

        df["created_at"] = pd.to_datetime(
            df["created_at"], errors="raise"
        )

    elif table_name == "dim_products":
        df["product_id"] = pd.to_numeric(
            df["product_id"], errors="raise"
        ).astype("int64")

        df["price"] = pd.to_numeric(
            df["price"], errors="raise"
        )

        df["created_at"] = pd.to_datetime(
            df["created_at"], errors="raise"
        )

    elif table_name == "fact_orders":
        df["order_id"] = pd.to_numeric(
            df["order_id"], errors="raise"
        ).astype("int64")

        df["customer_id"] = pd.to_numeric(
            df["customer_id"], errors="raise"
        ).astype("int64")

        df["total_amount"] = pd.to_numeric(
            df["total_amount"], errors="raise"
        )

        df["item_count"] = pd.to_numeric(
            df["item_count"], errors="raise"
        ).astype("int64")

        df["total_quantity"] = pd.to_numeric(
            df["total_quantity"], errors="raise"
        ).astype("int64")

        df["order_date"] = pd.to_datetime(
            df["order_date"], errors="raise"
        )

    elif table_name == "fact_order_items":
        df["order_item_id"] = pd.to_numeric(
            df["order_item_id"], errors="raise"
        ).astype("int64")

        df["order_id"] = pd.to_numeric(
            df["order_id"], errors="raise"
        ).astype("int64")

        df["product_id"] = pd.to_numeric(
            df["product_id"], errors="raise"
        ).astype("int64")

        df["quantity"] = pd.to_numeric(
            df["quantity"], errors="raise"
        ).astype("int64")

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

    with engine.begin() as connection:
        connection.execute(
            query,
            df.to_dict(orient="records")
        )

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

    with engine.begin() as connection:
        connection.execute(
            query,
            df.to_dict(orient="records")
        )

    print(f"  Rows processed: {len(df)}")


def get_incremental_orders(df):
    watermark = get_watermark("fact_orders_load")

    print(f"  Current watermark: {watermark}")

    new_orders = df[
        df["order_date"] > watermark
    ].copy()

    print(f"  Rows after incremental filter: {len(new_orders)}")

    return new_orders


def load_fact_orders(connection, df):
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

    if df.empty:
        print("  No new orders to load.")
        return

    connection.execute(
        query,
        df.to_dict(orient="records")
    )

    print(f"  Rows loaded: {len(df)}")


def load_fact_order_items(connection, df, order_ids):
    new_items = df[
        df["order_id"].isin(order_ids)
    ].copy()

    print(f"  Rows after incremental filter: {len(new_items)}")

    if new_items.empty:
        print("  No new order items to load.")
        return

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

    connection.execute(
        query,
        new_items.to_dict(orient="records")
    )

    print(f"  Rows loaded: {len(new_items)}")


def verify_warehouse():
    tables = [
        "dim_customers",
        "dim_products",
        "fact_orders",
        "fact_order_items"
    ]

    for table in tables:
        query = text(f"SELECT COUNT(*) FROM {table}")

        with engine.connect() as connection:
            count = connection.execute(query).scalar()

        print(f"  {table}: {count} rows")


def main():
    print("STARTING GOLD → DATA WAREHOUSE LOAD")

    customers = pd.read_csv(
        GOLD_DIR / "dim_customers.csv"
    )
    customers = prepare_table(
        customers,
        "dim_customers"
    )

    print("\nLoading dim_customers...")
    print(f"  Rows read: {len(customers)}")
    load_dim_customers(customers)

    products = pd.read_csv(
        GOLD_DIR / "dim_products.csv"
    )
    products = prepare_table(
        products,
        "dim_products"
    )

    print("\nLoading dim_products...")
    print(f"  Rows read: {len(products)}")
    load_dim_products(products)

    orders = pd.read_csv(
        GOLD_DIR / "fact_orders.csv"
    )
    orders = prepare_table(
        orders,
        "fact_orders"
    )

    print("\nLoading fact_orders...")
    print(f"  Rows read: {len(orders)}")

    new_orders = get_incremental_orders(orders)

    items = pd.read_csv(
        GOLD_DIR / "fact_order_items.csv"
    )
    items = prepare_table(
        items,
        "fact_order_items"
    )

    print("\nLoading fact_order_items...")
    print(f"  Rows read: {len(items)}")

    new_order_ids = new_orders["order_id"].tolist()

    new_watermark = (
        new_orders["order_date"].max()
        if not new_orders.empty
        else None
    )

    with engine.begin() as connection:
        load_fact_orders(
            connection,
            new_orders
        )

        load_fact_order_items(
            connection,
            items,
            new_order_ids
        )

    if new_watermark is not None:
        update_watermark(
            "fact_orders_load",
            new_watermark
        )
        print(f"  Watermark updated to: {new_watermark}")

    print("\nVERIFYING WAREHOUSE")
    verify_warehouse()

    print("WAREHOUSE LOAD COMPLETED")


if __name__ == "__main__":
    main()