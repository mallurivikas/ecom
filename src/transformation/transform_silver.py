from pathlib import Path

import pandas as pd

from src.validation.validate_silver import validate_all


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"


TABLES = [
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
]


def standardize_columns(df):
    """
    Standardize column names:
    - remove leading/trailing whitespace
    - convert to lowercase
    - replace spaces with underscores
    """
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df


def clean_strings(df):
    """
    Remove leading/trailing whitespace from string columns.
    """
    for column in df.select_dtypes(include=["object"]).columns:
        df[column] = df[column].str.strip()

    return df


def transform_table(table_name):
    """
    Read one raw table and transform it.

    IMPORTANT:
    This function does NOT write to Silver.
    It only returns the transformed DataFrame.
    """

    print(f"Transforming {table_name}...")

    input_file = RAW_DIR / f"{table_name}.csv"

    df = pd.read_csv(input_file)

    original_rows = len(df)

    # Standardize column names
    df = standardize_columns(df)

    # Clean whitespace
    df = clean_strings(df)

    # Table-specific type conversions
    if table_name == "customers":

        df["customer_id"] = pd.to_numeric(
            df["customer_id"],
            errors="coerce"
        )

        df["created_at"] = pd.to_datetime(
            df["created_at"],
            errors="coerce"
        )

    elif table_name == "products":

        df["product_id"] = pd.to_numeric(
            df["product_id"],
            errors="coerce"
        )

        df["price"] = pd.to_numeric(
            df["price"],
            errors="coerce"
        )

        df["created_at"] = pd.to_datetime(
            df["created_at"],
            errors="coerce"
        )

    elif table_name == "orders":

        df["order_id"] = pd.to_numeric(
            df["order_id"],
            errors="coerce"
        )

        df["customer_id"] = pd.to_numeric(
            df["customer_id"],
            errors="coerce"
        )

        df["total_amount"] = pd.to_numeric(
            df["total_amount"],
            errors="coerce"
        )

        df["order_date"] = pd.to_datetime(
            df["order_date"],
            errors="coerce"
        )

    elif table_name == "order_items":

        df["order_item_id"] = pd.to_numeric(
            df["order_item_id"],
            errors="coerce"
        )

        df["order_id"] = pd.to_numeric(
            df["order_id"],
            errors="coerce"
        )

        df["product_id"] = pd.to_numeric(
            df["product_id"],
            errors="coerce"
        )

        df["quantity"] = pd.to_numeric(
            df["quantity"],
            errors="coerce"
        )

        df["unit_price"] = pd.to_numeric(
            df["unit_price"],
            errors="coerce"
        )

    elif table_name == "payments":

        df["payment_id"] = pd.to_numeric(
            df["payment_id"],
            errors="coerce"
        )

        df["order_id"] = pd.to_numeric(
            df["order_id"],
            errors="coerce"
        )

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

        df["payment_date"] = pd.to_datetime(
            df["payment_date"],
            errors="coerce"
        )

    print(f"  Input rows: {original_rows}")
    print(f"  Transformed rows: {len(df)}")
    print()

    return df


def main():

    print("=" * 60)
    print("STARTING TRANSFORMATION + VALIDATION")
    print("=" * 60)
    print()

    # ---------------------------------------------------------
    # STEP 1: Transform everything in memory
    # ---------------------------------------------------------

    transformed_data = {}

    for table in TABLES:
        transformed_data[table] = transform_table(table)

    # ---------------------------------------------------------
    # STEP 2: Validate everything
    # ---------------------------------------------------------

    print("=" * 60)
    print("STARTING VALIDATION")
    print("=" * 60)
    print()

    try:

        validate_all(transformed_data)

    except ValueError as error:

        print()
        print("=" * 60)
        print("VALIDATION FAILED")
        print("=" * 60)
        print()
        print(error)
        print()
        print("Silver files were NOT written.")
        print()

        return

    # ---------------------------------------------------------
    # STEP 3: Validation passed
    # ---------------------------------------------------------

    print()
    print("=" * 60)
    print("VALIDATION PASSED")
    print("=" * 60)
    print()

    # ---------------------------------------------------------
    # STEP 4: Now write Silver
    # ---------------------------------------------------------

    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    print("Writing Silver files...\n")

    for table, df in transformed_data.items():

        output_file = SILVER_DIR / f"{table}.csv"

        df.to_csv(
            output_file,
            index=False
        )

        print(f"  Saved: {output_file}")

    print()
    print("=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()