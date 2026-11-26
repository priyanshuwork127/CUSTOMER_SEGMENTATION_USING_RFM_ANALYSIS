
from pathlib import Path
import sqlite3
import pandas as pd
import pytest

# Project root directory
ROOT = Path(__file__).resolve().parents[1]

DB_PATH = ROOT / "database" / "rfm_analytics.db"
SQL_RESULTS = ROOT / "outputs" / "sql_results"
APP_PATH = ROOT / "app.py"

EXPECTED_TABLES = {
    "Fact_Transactions",
    "Dim_Customer",
    "Dim_Product",
    "Dim_Date",
    "Dim_Payment",
    "Dim_Order_Status",
}

EXPECTED_RFM_COLUMNS = {
    "customer_id",
    "city",
    "state",
    "acquisition_channel",
    "recency_days",
    "frequency",
    "monetary",
    "r_score",
    "f_score",
    "m_score",
    "rfm_score",
    "customer_segment",
}


@pytest.fixture
def connection():
    """Open the project SQLite database."""
    assert DB_PATH.exists(), f"Database not found: {DB_PATH}"

    conn = sqlite3.connect(DB_PATH)
    yield conn
    conn.close()


@pytest.fixture
def rfm_data():
    """Load the final customer RFM analysis CSV."""
    path = SQL_RESULTS / "q1_customer_rfm_segments.csv"
    assert path.exists(), f"RFM CSV not found: {path}"

    return pd.read_csv(path)


def test_database_exists():
    assert DB_PATH.exists()


def test_required_tables_exist(connection):
    result = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table'",
        connection
    )

    actual_tables = set(result["name"])
    assert EXPECTED_TABLES.issubset(actual_tables)


def test_database_row_counts(connection):
    expected_counts = {
        "Dim_Customer": 500,
        "Dim_Product": 80,
        "Fact_Transactions": 9978,
    }

    for table, expected in expected_counts.items():
        actual = pd.read_sql_query(
            f"SELECT COUNT(*) AS total FROM {table}",
            connection
        )["total"].iloc[0]

        assert actual == expected, (
            f"{table}: expected {expected}, got {actual}"
        )


def test_customer_primary_keys_are_unique(connection):
    result = pd.read_sql_query(
        """
        SELECT customer_id, COUNT(*) AS total
        FROM Dim_Customer
        GROUP BY customer_id
        HAVING COUNT(*) > 1
        """,
        connection
    )

    assert result.empty


def test_product_primary_keys_are_unique(connection):
    result = pd.read_sql_query(
        """
        SELECT product_id, COUNT(*) AS total
        FROM Dim_Product
        GROUP BY product_id
        HAVING COUNT(*) > 1
        """,
        connection
    )

    assert result.empty


def test_foreign_key_integrity(connection):
    result = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    assert result == [], f"Foreign key violations: {result}"


def test_rfm_columns_exist(rfm_data):
    assert EXPECTED_RFM_COLUMNS.issubset(set(rfm_data.columns))


def test_rfm_customer_ids_are_unique(rfm_data):
    assert rfm_data["customer_id"].is_unique


def test_rfm_values_are_not_missing(rfm_data):
    required = [
        "customer_id",
        "recency_days",
        "frequency",
        "monetary",
        "r_score",
        "f_score",
        "m_score",
        "customer_segment",
    ]

    assert not rfm_data[required].isnull().any().any()


def test_rfm_scores_are_between_one_and_five(rfm_data):
    for column in ["r_score", "f_score", "m_score"]:
        assert rfm_data[column].between(1, 5).all()


def test_rfm_combined_score_is_correct(rfm_data):
    expected = (
        rfm_data["r_score"].astype(int).astype(str)
        + rfm_data["f_score"].astype(int).astype(str)
        + rfm_data["m_score"].astype(int).astype(str)
    )

    actual = rfm_data["rfm_score"].astype(str)

    assert (expected == actual).all()


def test_rfm_metrics_are_valid(rfm_data):
    assert (rfm_data["recency_days"] >= 0).all()
    assert (rfm_data["frequency"] > 0).all()
    assert (rfm_data["monetary"] > 0).all()


def test_customer_segments_are_assigned(rfm_data):
    assert rfm_data["customer_segment"].notna().all()
    assert rfm_data["customer_segment"].astype(str).str.strip().ne("").all()


def test_expected_customer_count(rfm_data):
    # Earlier RFM output contained 497 customers.
    assert len(rfm_data) == 497


def test_sql_output_files_exist():
    expected_files = [
        "q1_customer_rfm_segments.csv",
        "q2_customer_segment_distribution.csv",
        "q3_top_10_customers_by_monetary.csv",
        "q4_revenue_by_product_category.csv",
        "q5_monthly_revenue.csv",
        "q6_revenue_by_state_and_channel.csv",
        "q7_month_over_month_revenue_lag.csv",
    ]

    for filename in expected_files:
        assert (SQL_RESULTS / filename).exists(), (
            f"Missing SQL output: {filename}"
        )


def test_streamlit_app_exists():
    assert APP_PATH.exists()


def test_streamlit_app_has_valid_python_syntax():
    source = APP_PATH.read_text(encoding="utf-8")
    compile(source, str(APP_PATH), "exec")
