import pandas as pd


EXPECTED_COLUMNS = {
    "customers": [
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "country",
        "created_at",
    ],
    "products": [
        "product_id",
        "product_name",
        "category",
        "price",
        "created_at",
    ],
    "orders": [
        "order_id",
        "customer_id",
        "order_date",
        "status",
        "total_amount",
    ],
    "order_items": [
        "order_item_id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
    ],
    "payments": [
        "payment_id",
        "order_id",
        "payment_method",
        "payment_status",
        "amount",
        "payment_date",
    ],
}


REQUIRED_COLUMNS = {
    "customers": [
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "created_at",
    ],
    "products": [
        "product_id",
        "product_name",
        "category",
        "price",
        "created_at",
    ],
    "orders": [
        "order_id",
        "customer_id",
        "order_date",
        "status",
        "total_amount",
    ],
    "order_items": [
        "order_item_id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
    ],
    "payments": [
        "payment_id",
        "order_id",
        "payment_method",
        "payment_status",
        "amount",
        "payment_date",
    ],
}


PRIMARY_KEYS = {
    "customers": "customer_id",
    "products": "product_id",
    "orders": "order_id",
    "order_items": "order_item_id",
    "payments": "payment_id",
}


def validate_columns(table_name, df):
    expected = EXPECTED_COLUMNS[table_name]
    actual = list(df.columns)

    if actual != expected:
        raise ValueError(
            f"{table_name}: column mismatch.\n"
            f"Expected: {expected}\n"
            f"Actual:   {actual}"
        )


def validate_not_empty(table_name, df):
    if df.empty:
        raise ValueError(
            f"{table_name}: table contains no rows."
        )


def validate_required_columns(table_name, df):
    required_columns = REQUIRED_COLUMNS[table_name]

    for column in required_columns:

        if df[column].isna().any():

            bad_rows = df[
                df[column].isna()
            ].index.tolist()

            raise ValueError(
                f"{table_name}: NULL/NaN values found "
                f"in required column '{column}'. "
                f"Rows: {bad_rows}"
            )


def validate_primary_key(
    table_name,
    df,
    primary_key
):
    if df[primary_key].isna().any():

        raise ValueError(
            f"{table_name}: NULL/NaN values found "
            f"in primary key '{primary_key}'."
        )

    if df[primary_key].duplicated().any():

        duplicates = (
            df.loc[
                df[primary_key].duplicated(
                    keep=False
                ),
                primary_key
            ]
            .tolist()
        )

        raise ValueError(
            f"{table_name}: duplicate primary key values "
            f"found in '{primary_key}': {duplicates}"
        )


def validate_positive_values(
    table_name,
    df,
    columns
):
    for column in columns:

        invalid = df[
            df[column] <= 0
        ]

        if not invalid.empty:

            raise ValueError(
                f"{table_name}: invalid values found "
                f"in '{column}'. Values must be > 0.\n"
                f"Invalid values: "
                f"{invalid[column].tolist()}"
            )


def validate_allowed_values(
    table_name,
    df,
    column,
    allowed_values
):
    invalid = df[
        ~df[column].isin(allowed_values)
    ]

    if not invalid.empty:

        values = (
            invalid[column]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            f"{table_name}: invalid values found "
            f"in '{column}': {values}\n"
            f"Allowed values: {allowed_values}"
        )


def validate_foreign_key(
    child_table,
    child_df,
    child_column,
    parent_table,
    parent_df,
    parent_column,
):
    invalid = child_df[
        ~child_df[child_column].isin(
            parent_df[parent_column]
        )
    ]

    if not invalid.empty:

        invalid_values = (
            invalid[child_column]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            f"{child_table}: invalid foreign key values "
            f"in '{child_column}'.\n"
            f"Values not found in "
            f"{parent_table}.{parent_column}: "
            f"{invalid_values}"
        )


def validate_business_rules(
    table_name,
    df
):
    if table_name == "products":

        validate_positive_values(
            table_name,
            df,
            ["price"]
        )

    elif table_name == "orders":

        validate_positive_values(
            table_name,
            df,
            ["total_amount"]
        )

        validate_allowed_values(
            table_name,
            df,
            "status",
            [
                "PENDING",
                "COMPLETED",
                "CANCELLED",
            ]
        )

    elif table_name == "order_items":

        validate_positive_values(
            table_name,
            df,
            [
                "quantity",
                "unit_price",
            ]
        )

    elif table_name == "payments":

        validate_positive_values(
            table_name,
            df,
            ["amount"]
        )

        validate_allowed_values(
            table_name,
            df,
            "payment_method",
            [
                "UPI",
                "CREDIT_CARD",
                "DEBIT_CARD",
            ]
        )

        validate_allowed_values(
            table_name,
            df,
            "payment_status",
            [
                "PENDING",
                "SUCCESS",
                "REFUNDED",
            ]
        )


def validate_relationships(data):

    validate_foreign_key(
        "orders",
        data["orders"],
        "customer_id",
        "customers",
        data["customers"],
        "customer_id",
    )

    validate_foreign_key(
        "order_items",
        data["order_items"],
        "order_id",
        "orders",
        data["orders"],
        "order_id",
    )

    validate_foreign_key(
        "order_items",
        data["order_items"],
        "product_id",
        "products",
        data["products"],
        "product_id",
    )

    validate_foreign_key(
        "payments",
        data["payments"],
        "order_id",
        "orders",
        data["orders"],
        "order_id",
    )


def validate_table(
    table_name,
    df
):
    print(f"Validating {table_name}...")

    validate_columns(
        table_name,
        df
    )

    validate_not_empty(
        table_name,
        df
    )

    validate_required_columns(
        table_name,
        df
    )

    validate_primary_key(
        table_name,
        df,
        PRIMARY_KEYS[table_name]
    )

    validate_business_rules(
        table_name,
        df
    )

    print(
        f"  ✓ {table_name} passed table validation"
    )

    print(
        f"  Rows: {len(df)}"
    )

    print()


def validate_all(data):
    """
    Validate all transformed DataFrames
    before they are written to Silver.
    """

    print("Validating tables...\n")

    # -----------------------------------------
    # Table-level validation
    # -----------------------------------------

    for table_name, df in data.items():

        validate_table(
            table_name,
            df
        )

    # -----------------------------------------
    # Relationship validation
    # -----------------------------------------

    print("Validating relationships...\n")

    validate_relationships(data)

    print(
        "✓ All validation checks passed."
    )