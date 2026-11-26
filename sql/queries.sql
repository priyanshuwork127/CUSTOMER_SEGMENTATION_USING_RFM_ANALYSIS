-- P8: Seven business questions for Customer Segmentation using RFM Analysis
-- Reference date: 2026-11-01
-- Revenue and RFM Monetary include Completed transactions only.
-- Frequency = COUNT(DISTINCT invoice_id), not transaction/product-line count.

-- QUERY: q1_customer_rfm_segments
-- Q1. What are each customer's Recency, Frequency, Monetary value, RFM scores and segment?
WITH customer_rfm AS (
    SELECT
        c.customer_id,
        c.city,
        c.state,
        c.acquisition_channel,
        CAST(julianday('2026-11-01') - julianday(MAX(d.full_date)) AS INTEGER) AS recency_days,
        COUNT(DISTINCT f.invoice_id) AS frequency,
        ROUND(SUM(f.net_amount), 2) AS monetary
    FROM Fact_Transactions f
    JOIN Dim_Customer c ON f.customer_key = c.customer_key
    JOIN Dim_Date d ON f.date_key = d.date_key
    JOIN Dim_Order_Status s ON f.status_key = s.status_key
    WHERE s.order_status = 'Completed'
    GROUP BY c.customer_id, c.city, c.state, c.acquisition_channel
),
scored AS (
    SELECT *,
        6 - NTILE(5) OVER (ORDER BY recency_days ASC, customer_id) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC, customer_id) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC, customer_id) AS m_score
    FROM customer_rfm
),
segmented AS (
    SELECT *,
        (r_score * 100 + f_score * 10 + m_score) AS rfm_score,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN f_score >= 4 AND r_score >= 3 THEN 'Loyal Customers'
            WHEN r_score = 5 AND f_score = 1 THEN 'New Customers'
            WHEN r_score >= 4 AND f_score >= 2 THEN 'Potential Loyalists'
            WHEN r_score <= 2 AND (f_score >= 3 OR m_score >= 3) THEN 'At Risk'
            WHEN r_score <= 2 AND f_score <= 2 THEN 'Hibernating'
            ELSE 'Need Attention'
        END AS customer_segment
    FROM scored
)
SELECT *
FROM segmented
ORDER BY rfm_score DESC, monetary DESC;

-- QUERY: q2_customer_segment_distribution
-- Q2. How many customers belong to each RFM segment?
WITH customer_rfm AS (
    SELECT
        c.customer_id,
        CAST(julianday('2026-11-01') - julianday(MAX(d.full_date)) AS INTEGER) AS recency_days,
        COUNT(DISTINCT f.invoice_id) AS frequency,
        SUM(f.net_amount) AS monetary
    FROM Fact_Transactions f
    JOIN Dim_Customer c ON f.customer_key = c.customer_key
    JOIN Dim_Date d ON f.date_key = d.date_key
    JOIN Dim_Order_Status s ON f.status_key = s.status_key
    WHERE s.order_status = 'Completed'
    GROUP BY c.customer_id
),
scored AS (
    SELECT *,
        6 - NTILE(5) OVER (ORDER BY recency_days ASC, customer_id) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC, customer_id) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC, customer_id) AS m_score
    FROM customer_rfm
),
segmented AS (
    SELECT *,
        (r_score * 100 + f_score * 10 + m_score) AS rfm_score,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN f_score >= 4 AND r_score >= 3 THEN 'Loyal Customers'
            WHEN r_score = 5 AND f_score = 1 THEN 'New Customers'
            WHEN r_score >= 4 AND f_score >= 2 THEN 'Potential Loyalists'
            WHEN r_score <= 2 AND (f_score >= 3 OR m_score >= 3) THEN 'At Risk'
            WHEN r_score <= 2 AND f_score <= 2 THEN 'Hibernating'
            ELSE 'Need Attention'
        END AS customer_segment
    FROM scored
)
SELECT
    customer_segment,
    COUNT(*) AS customer_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS customer_percentage
FROM segmented
GROUP BY customer_segment
ORDER BY customer_count DESC;

-- QUERY: q3_top_10_customers_by_monetary
-- Q3. Who are the top 10 customers by completed-purchase monetary value?
SELECT
    c.customer_id,
    c.city,
    c.state,
    COUNT(DISTINCT f.invoice_id) AS frequency,
    ROUND(SUM(f.net_amount), 2) AS monetary
FROM Fact_Transactions f
JOIN Dim_Customer c ON f.customer_key = c.customer_key
JOIN Dim_Order_Status s ON f.status_key = s.status_key
WHERE s.order_status = 'Completed'
GROUP BY c.customer_id, c.city, c.state
ORDER BY monetary DESC
LIMIT 10;

-- QUERY: q4_revenue_by_product_category
-- Q4. Which product categories generate the highest completed-purchase revenue?
SELECT
    p.category,
    COUNT(DISTINCT f.invoice_id) AS invoice_count,
    SUM(f.quantity) AS units_sold,
    ROUND(SUM(f.net_amount), 2) AS net_revenue
FROM Fact_Transactions f
JOIN Dim_Product p ON f.product_key = p.product_key
JOIN Dim_Order_Status s ON f.status_key = s.status_key
WHERE s.order_status = 'Completed'
GROUP BY p.category
ORDER BY net_revenue DESC;

-- QUERY: q5_monthly_revenue
-- Q5. What is the monthly trend in completed-purchase revenue?
SELECT
    strftime('%Y-%m', d.full_date) AS sales_month,
    COUNT(DISTINCT f.invoice_id) AS invoice_count,
    ROUND(SUM(f.net_amount), 2) AS monthly_revenue
FROM Fact_Transactions f
JOIN Dim_Date d ON f.date_key = d.date_key
JOIN Dim_Order_Status s ON f.status_key = s.status_key
WHERE s.order_status = 'Completed'
GROUP BY strftime('%Y-%m', d.full_date)
ORDER BY sales_month;

-- QUERY: q6_revenue_by_state_and_channel
-- Q6. How does completed-purchase revenue vary by customer state and acquisition channel?
SELECT
    c.state,
    c.acquisition_channel,
    COUNT(DISTINCT c.customer_id) AS purchasing_customers,
    COUNT(DISTINCT f.invoice_id) AS invoice_count,
    ROUND(SUM(f.net_amount), 2) AS net_revenue
FROM Fact_Transactions f
JOIN Dim_Customer c ON f.customer_key = c.customer_key
JOIN Dim_Order_Status s ON f.status_key = s.status_key
WHERE s.order_status = 'Completed'
GROUP BY c.state, c.acquisition_channel
ORDER BY net_revenue DESC;

-- QUERY: q7_month_over_month_revenue_lag
-- Q7. How much did monthly revenue change compared with the previous month? (LAG window function)
WITH monthly_sales AS (
    SELECT
        strftime('%Y-%m', d.full_date) AS sales_month,
        SUM(f.net_amount) AS monthly_revenue
    FROM Fact_Transactions f
    JOIN Dim_Date d ON f.date_key = d.date_key
    JOIN Dim_Order_Status s ON f.status_key = s.status_key
    WHERE s.order_status = 'Completed'
    GROUP BY strftime('%Y-%m', d.full_date)
),
with_previous_month AS (
    SELECT
        sales_month,
        monthly_revenue,
        LAG(monthly_revenue) OVER (ORDER BY sales_month) AS previous_month_revenue
    FROM monthly_sales
)
SELECT
    sales_month,
    ROUND(monthly_revenue, 2) AS monthly_revenue,
    ROUND(previous_month_revenue, 2) AS previous_month_revenue,
    ROUND(monthly_revenue - previous_month_revenue, 2) AS revenue_change,
    CASE
        WHEN previous_month_revenue IS NULL THEN 'No previous month'
        WHEN monthly_revenue > previous_month_revenue THEN 'Growth'
        WHEN monthly_revenue < previous_month_revenue THEN 'Decline'
        ELSE 'No Change'
    END AS revenue_movement
FROM with_previous_month
ORDER BY sales_month;
