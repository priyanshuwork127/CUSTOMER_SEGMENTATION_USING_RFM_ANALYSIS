"""P8: Load cleaned RFM project CSV files into SQLite and export SQL results."""

from pathlib import Path
import re
import sqlite3
import sys

import pandas as pd


# Project paths are resolved relative to this script's location.
PROJECT_DIR = Path(__file__).resolve().parents[1]
CLEAN_DIR = PROJECT_DIR / "data" / "clean"
SQL_DIR = PROJECT_DIR / "sql"
DATABASE_DIR = PROJECT_DIR / "database"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "sql_results"

SCHEMA_FILE = SQL_DIR / "schema.sql"
QUERIES_FILE = SQL_DIR / "queries.sql"
DB_FILE = DATABASE_DIR / "rfm_analytics.db"

REFERENCE_DATE = pd.Timestamp("2026-11-01")


def read_csv(filename: str) -> pd.DataFrame:
    path = CLEAN_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Required cleaned CSV not found: {path}")
    return pd.read_csv(path)


def load_dimensions(connection: sqlite3.Connection):
    customers = read_csv("customers.csv")
    products = read_csv("products.csv")
    transactions = read_csv("transactions.csv")

    # Customer dimension
    customers = customers.copy()
    customers["customer_key"] = range(1, len(customers) + 1)
    for column in ["city", "state", "acquisition_channel"]:
        customers[column] = customers[column].fillna("Unknown").astype(str)
    customers["signup_date"] = pd.to_datetime(
        customers["signup_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    connection.executemany(
        """INSERT INTO Dim_Customer
           (customer_key, customer_id, signup_date, city, state, acquisition_channel)
           VALUES (?, ?, ?, ?, ?, ?)""",
        customers[[
            "customer_key", "customer_id", "signup_date", "city", "state",
            "acquisition_channel"
        ]].itertuples(index=False, name=None)
    )
    customer_key_map = dict(zip(customers["customer_id"], customers["customer_key"]))

    # Product dimension
    products = products.copy()
    products["product_key"] = range(1, len(products) + 1)
    products["product_name"] = products["product_name"].fillna("Unknown")
    products["category"] = products["category"].fillna("Unknown")
    connection.executemany(
        """INSERT INTO Dim_Product
           (product_key, product_id, product_name, category, standard_unit_price)
           VALUES (?, ?, ?, ?, ?)""",
        products[[
            "product_key", "product_id", "product_name", "category", "unit_price"
        ]].itertuples(index=False, name=None)
    )
    product_key_map = dict(zip(products["product_id"], products["product_key"]))

    # Payment dimension: distinct canonical values in the cleaned transactions.
    payment_methods = sorted(transactions["payment_method"].fillna("Unknown").astype(str).unique())
    connection.executemany(
        "INSERT INTO Dim_Payment (payment_key, payment_method) VALUES (?, ?)",
        [(i, value) for i, value in enumerate(payment_methods, start=1)]
    )
    payment_key_map = {value: i for i, value in enumerate(payment_methods, start=1)}

    # Status dimension
    statuses = ["Cancelled", "Completed", "Returned"]
    connection.executemany(
        "INSERT INTO Dim_Order_Status (status_key, order_status) VALUES (?, ?)",
        [(i, value) for i, value in enumerate(statuses, start=1)]
    )
    status_key_map = {value: i for i, value in enumerate(statuses, start=1)}

    # Date dimension: populate every calendar date between min and max transaction dates.
    transactions["invoice_date"] = pd.to_datetime(
        transactions["invoice_date"], errors="coerce"
    )
    if transactions["invoice_date"].isna().any():
        raise ValueError("Clean transactions still contain invalid invoice_date values.")

    min_date = transactions["invoice_date"].min().normalize()
    max_date = transactions["invoice_date"].max().normalize()
    all_dates = pd.date_range(min_date, max_date, freq="D")

    date_rows = []
    date_key_map = {}
    for date_value in all_dates:
        date_text = date_value.strftime("%Y-%m-%d")
        date_key = int(date_value.strftime("%Y%m%d"))
        date_key_map[date_text] = date_key
        date_rows.append((
            date_key,
            date_text,
            date_value.year,
            ((date_value.month - 1) // 3) + 1,
            date_value.month,
            date_value.strftime("%B"),
            date_value.day,
            date_value.strftime("%A")
        ))

    connection.executemany(
        """INSERT INTO Dim_Date
           (date_key, full_date, calendar_year, quarter_number,
            month_number, month_name, day_of_month, day_name)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        date_rows
    )

    return (transactions, customer_key_map, product_key_map,
            date_key_map, payment_key_map, status_key_map)


def load_fact(connection: sqlite3.Connection, loaded_dimensions):
    (transactions, customer_map, product_map,
     date_map, payment_map, status_map) = loaded_dimensions

    fact_rows = []
    missing_reference_rows = []

    for row in transactions.itertuples(index=False):
        customer_id = str(row.customer_id)
        product_id = str(row.product_id)
        invoice_date = row.invoice_date.strftime("%Y-%m-%d")
        payment_method = str(row.payment_method) if pd.notna(row.payment_method) else "Unknown"
        order_status = str(row.order_status)

        if (customer_id not in customer_map or product_id not in product_map
                or invoice_date not in date_map or payment_method not in payment_map
                or order_status not in status_map):
            missing_reference_rows.append(row.invoice_id)
            continue

        quantity = int(row.quantity)
        unit_price = float(row.unit_price)
        discount_pct = float(row.discount_pct)
        gross_amount = quantity * unit_price
        discount_amount = gross_amount * discount_pct
        net_amount = gross_amount - discount_amount

        fact_rows.append((
            str(row.invoice_id),
            customer_map[customer_id],
            product_map[product_id],
            date_map[invoice_date],
            payment_map[payment_method],
            status_map[order_status],
            quantity,
            unit_price,
            discount_pct,
            gross_amount,
            discount_amount,
            net_amount
        ))

    if missing_reference_rows:
        raise ValueError(
            f"Found {len(missing_reference_rows)} fact rows with missing dimension references. "
            "Check cleaned CSV relationships before loading."
        )

    connection.executemany(
        """INSERT INTO Fact_Transactions
           (invoice_id, customer_key, product_key, date_key, payment_key,
            status_key, quantity, unit_price, discount_pct, gross_amount,
            discount_amount, net_amount)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        fact_rows
    )
    return len(fact_rows)


def split_queries(sql_text: str):
    """Split queries using explicit '-- QUERY: query_name' markers."""
    pattern = re.compile(r"^\s*--\s*QUERY:\s*([A-Za-z0-9_]+)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(sql_text))
    if not matches:
        raise ValueError("No '-- QUERY: query_name' markers found in queries.sql")

    queries = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(sql_text)
        query_sql = sql_text[start:end].strip()
        # Remove leading descriptive comments; retain SQL and internal comments.
        query_sql = "\n".join(
            line for line in query_sql.splitlines()
            if not line.lstrip().startswith("--")
        ).strip()
        if query_sql:
            queries.append((match.group(1), query_sql))
    return queries


def run_queries(connection: sqlite3.Connection):
    sql_text = QUERIES_FILE.read_text(encoding="utf-8")
    queries = split_queries(sql_text)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for query_name, query_sql in queries:
        result = pd.read_sql_query(query_sql, connection)
        output_file = OUTPUT_DIR / f"{query_name}.csv"
        result.to_csv(output_file, index=False)
        print(f"{query_name}: {len(result):,} rows -> {output_file.relative_to(PROJECT_DIR)}")

    print(f"\nExecuted and exported {len(queries)} SQL queries.")


def main():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")
    if not QUERIES_FILE.exists():
        raise FileNotFoundError(f"Queries file not found: {QUERIES_FILE}")

    # Rebuild the database each time to avoid duplicate inserts on reruns.
    if DB_FILE.exists():
        DB_FILE.unlink()

    print("Creating SQLite database...")
    with sqlite3.connect(DB_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        connection.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))

        dimensions = load_dimensions(connection)
        fact_count = load_fact(connection, dimensions)
        connection.commit()

        # Verify foreign-key integrity.
        fk_errors = connection.execute("PRAGMA foreign_key_check;").fetchall()
        if fk_errors:
            raise RuntimeError(f"Foreign-key validation failed: {fk_errors[:5]}")

        print("\nDatabase loaded successfully:")
        for table in [
            "Dim_Customer", "Dim_Product", "Dim_Date", "Dim_Payment",
            "Dim_Order_Status", "Fact_Transactions"
        ]:
            count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table}: {count:,} rows")

        print(f"  Fact rows inserted: {fact_count:,}")
        run_queries(connection)

    print("\nP8 completed successfully.")
    print(f"Database: {DB_FILE}")
    print(f"Query outputs: {OUTPUT_DIR}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nERROR: {error}")
        sys.exit(1)
