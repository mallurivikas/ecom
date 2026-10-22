from pathlib import Path

import pandas as pd

from src.validation.validate_gold import validate_gold


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"


def load_silver(table_name):
    """Load a Silver table."""
    file_path = SILVER_DIR / f"{table_name}.csv"

    print(f"Loading {table_name}...")
    df = pd.read_csv(file_path)

    print(f"  Rows: {len(df)}")

    return df


def create_dim_customers(customers):
    """
    Create customer dimension.

    Grain:
        One row per customer.
    """

    return customers[
        [
            "customer_id",
            "first_name",
            "last_name",
            "email",
            "country",
            "created_at",
        ]
    ].copy()


def create_dim_products(products):
    """
    Create product dimension.

    Grain:
        One row per product.
    """

    return products[
        [
            "product_id",
            "product_name",
            "category",
            "price",
            "created_at",
        ]
    ].copy()


def create_fact_order_items(order_items):
    """
    Create order-item fact table.

    Grain:
        One row per order item.

    Derived measure:
        item_total = quantity * unit_price
    """

    fact_order_items = order_items[
        [
            "order_item_id",
            "order_id",
            "product_id",
            "quantity",
            "unit_price",
        ]
    ].copy()

    fact_order_items["item_total"] = (
        fact_order_items["quantity"]
        * fact_order_items["unit_price"]
    )

    return fact_order_items


def create_fact_orders(orders, order_items):
    """
    Create order fact table.

    Grain:
        One row per order.

    Derived measures:
        item_count
        total_quantity
    """

    fact_orders = orders[
        [
            "order_id",
            "customer_id",
            "order_date",
            "status",
            "total_amount",
        ]
    ].copy()

    order_metrics = (
        order_items
        .groupby("order_id")
        .agg(
            item_count=("order_item_id", "count"),
            total_quantity=("quantity", "sum"),
        )
        .reset_index()
    )

    fact_orders = fact_orders.merge(
        order_metrics,
        on="order_id",
        how="left",
    )

    fact_orders["item_count"] = (
        fact_orders["item_count"]
        .fillna(0)
        .astype(int)
    )

    fact_orders["total_quantity"] = (
        fact_orders["total_quantity"]
        .fillna(0)
        .astype(int)
    )

    return fact_orders


def main():
    print("=" * 60)
    print("STARTING GOLD TRANSFORMATION")
    print("=" * 60)
    print()

    customers = load_silver("customers")
    products = load_silver("products")
    orders = load_silver("orders")
    order_items = load_silver("order_items")

    print()

    print("=" * 60)
    print("CREATING GOLD TABLES")
    print("=" * 60)
    print()

    dim_customers = create_dim_customers(customers)

    dim_products = create_dim_products(products)

    fact_order_items = create_fact_order_items(order_items)

    fact_orders = create_fact_orders(
        orders,
        order_items,
    )

    gold_data = {
        "dim_customers": dim_customers,
        "dim_products": dim_products,
        "fact_orders": fact_orders,
        "fact_order_items": fact_order_items,
    }

    print("Gold table summary:")
    print()

    for table_name, df in gold_data.items():
        print(f"{table_name}: {len(df)} rows")

    print()
    print("=" * 60)
    print("VALIDATING GOLD")
    print("=" * 60)
    print()

    try:
        validate_gold(gold_data)

    except ValueError as error:
        print()
        print("=" * 60)
        print("GOLD VALIDATION FAILED")
        print("=" * 60)
        print()
        print(error)
        print()
        print("Gold files were NOT written.")
        print()

        return

    print()
    print("=" * 60)
    print("GOLD VALIDATION PASSED")
    print("=" * 60)
    print()

    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    print("Writing Gold files...")
    print()

    for table_name, df in gold_data.items():
        output_file = GOLD_DIR / f"{table_name}.csv"

        df.to_csv(
            output_file,
            index=False,
        )

        print(f"Saved: {output_file}")

    print()
    print("=" * 60)
    print("GOLD TRANSFORMATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()