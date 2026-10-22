import pandas as pd


def require_columns(df, table_name, expected_columns):
    """Validate that a table contains exactly the expected columns."""

    actual_columns = list(df.columns)

    if actual_columns != expected_columns:
        raise ValueError(
            f"{table_name}: unexpected columns.\n"
            f"Expected: {expected_columns}\n"
            f"Actual:   {actual_columns}"
        )


def validate_not_empty(data):
    """Validate that Gold tables are not empty."""

    for table_name, df in data.items():

        if df.empty:
            raise ValueError(
                f"{table_name}: table is empty."
            )


def validate_primary_keys(data):
    """Validate primary-key uniqueness."""

    primary_keys = {
        "dim_customers": "customer_id",
        "dim_products": "product_id",
        "fact_orders": "order_id",
        "fact_order_items": "order_item_id",
    }

    for table_name, primary_key in primary_keys.items():

        df = data[table_name]

        if df[primary_key].isna().any():
            raise ValueError(
                f"{table_name}: "
                f"{primary_key} contains NULL values."
            )

        if df[primary_key].duplicated().any():
            duplicates = (
                df.loc[
                    df[primary_key].duplicated(keep=False),
                    primary_key,
                ]
                .tolist()
            )

            raise ValueError(
                f"{table_name}: duplicate "
                f"{primary_key} values found: {duplicates}"
            )


def validate_foreign_keys(data):
    """Validate relationships between Gold tables."""

    dim_customers = data["dim_customers"]
    dim_products = data["dim_products"]
    fact_orders = data["fact_orders"]
    fact_order_items = data["fact_order_items"]

    customer_ids = set(
        dim_customers["customer_id"]
    )

    product_ids = set(
        dim_products["product_id"]
    )

    order_ids = set(
        fact_orders["order_id"]
    )

    invalid_customers = set(
        fact_orders["customer_id"]
    ) - customer_ids

    if invalid_customers:
        raise ValueError(
            "fact_orders: customer_id values "
            f"not found in dim_customers: "
            f"{sorted(invalid_customers)}"
        )

    invalid_orders = set(
        fact_order_items["order_id"]
    ) - order_ids

    if invalid_orders:
        raise ValueError(
            "fact_order_items: order_id values "
            f"not found in fact_orders: "
            f"{sorted(invalid_orders)}"
        )

    invalid_products = set(
        fact_order_items["product_id"]
    ) - product_ids

    if invalid_products:
        raise ValueError(
            "fact_order_items: product_id values "
            f"not found in dim_products: "
            f"{sorted(invalid_products)}"
        )


def validate_item_totals(data):
    """
    Validate the Gold-derived item_total measure.

    item_total must equal:
        quantity * unit_price
    """

    fact_order_items = data["fact_order_items"]

    calculated_total = (
        fact_order_items["quantity"]
        * fact_order_items["unit_price"]
    )

    mismatches = (
        fact_order_items["item_total"]
        != calculated_total
    )

    if mismatches.any():

        bad_rows = fact_order_items.loc[
            mismatches,
            [
                "order_item_id",
                "quantity",
                "unit_price",
                "item_total",
            ],
        ]

        raise ValueError(
            "fact_order_items: item_total "
            "calculation mismatch.\n"
            f"{bad_rows.to_string(index=False)}"
        )


def validate_order_metrics(data):
    """
    Validate order-level Gold metrics.

    item_count must equal the number of order items.

    total_quantity must equal the sum of quantities.
    """

    fact_orders = data["fact_orders"]
    fact_order_items = data["fact_order_items"]

    calculated_metrics = (
        fact_order_items
        .groupby("order_id")
        .agg(
            expected_item_count=("order_item_id", "count"),
            expected_total_quantity=("quantity", "sum"),
        )
    )

    for _, order in fact_orders.iterrows():

        order_id = order["order_id"]

        expected = calculated_metrics.loc[order_id]

        if order["item_count"] != expected["expected_item_count"]:
            raise ValueError(
                f"fact_orders: item_count mismatch "
                f"for order_id {order_id}.\n"
                f"Gold value = {order['item_count']}\n"
                f"Calculated value = "
                f"{expected['expected_item_count']}"
            )

        if order["total_quantity"] != expected["expected_total_quantity"]:
            raise ValueError(
                f"fact_orders: total_quantity mismatch "
                f"for order_id {order_id}.\n"
                f"Gold value = {order['total_quantity']}\n"
                f"Calculated value = "
                f"{expected['expected_total_quantity']}"
            )


def validate_grain(data):
    """Validate the declared grain of each fact table."""

    fact_orders = data["fact_orders"]

    fact_order_items = data["fact_order_items"]

    if len(fact_orders) != fact_orders["order_id"].nunique():
        raise ValueError(
            "fact_orders: grain violation. "
            "Expected one row per order."
        )

    if len(fact_order_items) != (
        fact_order_items["order_item_id"].nunique()
    ):
        raise ValueError(
            "fact_order_items: grain violation. "
            "Expected one row per order item."
        )


def validate_expected_columns(data):
    """Validate the Gold table schemas."""

    expected_columns = {
        "dim_customers": [
            "customer_id",
            "first_name",
            "last_name",
            "email",
            "country",
            "created_at",
        ],
        "dim_products": [
            "product_id",
            "product_name",
            "category",
            "price",
            "created_at",
        ],
        "fact_orders": [
            "order_id",
            "customer_id",
            "order_date",
            "status",
            "total_amount",
            "item_count",
            "total_quantity",
        ],
        "fact_order_items": [
            "order_item_id",
            "order_id",
            "product_id",
            "quantity",
            "unit_price",
            "item_total",
        ],
    }

    for table_name, columns in expected_columns.items():
        require_columns(
            data[table_name],
            table_name,
            columns,
        )


def validate_gold(data):
    """
    Run all Gold validations.

    Gold validation verifies the result of the
    Gold transformation, not the Silver layer.
    """

    validate_expected_columns(data)

    validate_not_empty(data)

    validate_primary_keys(data)

    validate_foreign_keys(data)

    validate_grain(data)

    validate_item_totals(data)

    validate_order_metrics(data)

    print("All Gold validations passed.")