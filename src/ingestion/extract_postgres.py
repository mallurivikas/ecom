import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# Create database connection
DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)


# Source tables to extract
TABLES = [
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
]


# Raw data directory
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def extract_table(table_name):
    print(f"Extracting {table_name}...")

    query = f"SELECT * FROM {table_name}"

    df = pd.read_sql(query, engine)

    output_file = RAW_DIR / f"{table_name}.csv"

    df.to_csv(output_file, index=False)

    print(
        f"  Rows extracted: {len(df)}"
    )
    print(
        f"  Saved to: {output_file}"
    )


def main():
    print("Starting PostgreSQL extraction...\n")

    for table in TABLES:
        extract_table(table)

    print("\nExtraction completed successfully.")


if __name__ == "__main__":
    main()