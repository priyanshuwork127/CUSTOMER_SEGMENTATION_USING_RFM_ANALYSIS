-- P7: Star schema for Customer Segmentation using RFM
-- SQLite DDL
-- Fact grain: one row per product line within an invoice.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Dim_Customer (
    customer_key INTEGER PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE,
    signup_date TEXT,
    city TEXT NOT NULL DEFAULT 'Unknown',
    state TEXT NOT NULL DEFAULT 'Unknown',
    acquisition_channel TEXT NOT NULL DEFAULT 'Unknown',
    CHECK (length(trim(customer_id)) > 0)
);

CREATE TABLE IF NOT EXISTS Dim_Product (
    product_key INTEGER PRIMARY KEY,
    product_id TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    standard_unit_price REAL NOT NULL,
    CHECK (length(trim(product_id)) > 0),
    CHECK (standard_unit_price > 0)
);

CREATE TABLE IF NOT EXISTS Dim_Date (
    date_key INTEGER PRIMARY KEY, -- YYYYMMDD, e.g. 20261031
    full_date TEXT NOT NULL UNIQUE,
    calendar_year INTEGER NOT NULL,
    quarter_number INTEGER NOT NULL,
    month_number INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    CHECK (calendar_year BETWEEN 2000 AND 2100),
    CHECK (quarter_number BETWEEN 1 AND 4),
    CHECK (month_number BETWEEN 1 AND 12),
    CHECK (day_of_month BETWEEN 1 AND 31)
);

CREATE TABLE IF NOT EXISTS Dim_Payment (
    payment_key INTEGER PRIMARY KEY,
    payment_method TEXT NOT NULL UNIQUE,
    CHECK (length(trim(payment_method)) > 0)
);

CREATE TABLE IF NOT EXISTS Dim_Order_Status (
    status_key INTEGER PRIMARY KEY,
    order_status TEXT NOT NULL UNIQUE,
    CHECK (order_status IN ('Completed', 'Cancelled', 'Returned'))
);

CREATE TABLE IF NOT EXISTS Fact_Transactions (
    transaction_key INTEGER PRIMARY KEY,
    invoice_id TEXT NOT NULL, -- degenerate dimension; repeats across invoice lines
    customer_key INTEGER NOT NULL,
    product_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    payment_key INTEGER NOT NULL,
    status_key INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    discount_pct REAL NOT NULL DEFAULT 0,
    gross_amount REAL NOT NULL,
    discount_amount REAL NOT NULL,
    net_amount REAL NOT NULL,

    CONSTRAINT fk_fact_customer
        FOREIGN KEY (customer_key) REFERENCES Dim_Customer(customer_key),
    CONSTRAINT fk_fact_product
        FOREIGN KEY (product_key) REFERENCES Dim_Product(product_key),
    CONSTRAINT fk_fact_date
        FOREIGN KEY (date_key) REFERENCES Dim_Date(date_key),
    CONSTRAINT fk_fact_payment
        FOREIGN KEY (payment_key) REFERENCES Dim_Payment(payment_key),
    CONSTRAINT fk_fact_status
        FOREIGN KEY (status_key) REFERENCES Dim_Order_Status(status_key),

    CHECK (length(trim(invoice_id)) > 0),
    CHECK (quantity <> 0),
    CHECK (unit_price > 0),
    CHECK (discount_pct BETWEEN 0 AND 1),
    CHECK (ABS(net_amount - (gross_amount - discount_amount)) < 0.02)
);

-- Helpful indexes for common joins and RFM filtering.
CREATE INDEX IF NOT EXISTS idx_fact_customer
    ON Fact_Transactions(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_product
    ON Fact_Transactions(product_key);
CREATE INDEX IF NOT EXISTS idx_fact_date
    ON Fact_Transactions(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_status
    ON Fact_Transactions(status_key);
CREATE INDEX IF NOT EXISTS idx_fact_invoice
    ON Fact_Transactions(invoice_id);
