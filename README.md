# Customer Segmentation Using RFM Analysis

**Developed by:** Priyanshu  
**Batch:** 16  
**Institution:** ABES Engineering College  
**Email:** priyanshu.25b15410254@abes.ac.in

## Project Overview

This project performs customer segmentation using Recency, Frequency and Monetary (RFM) analysis. It transforms e-commerce transaction data into meaningful customer groups and business insights.

## Objectives

- Clean and prepare e-commerce transaction data.
- Calculate customer-level RFM metrics.
- Assign RFM scores and customer segments.
- Store analytical data in a SQLite database.
- Perform business analysis using SQL.
- Build an interactive Streamlit dashboard.
- Validate the project using automated tests.

## Technologies Used

- Python
- Pandas and NumPy
- SQLite and SQL
- Matplotlib and Seaborn
- Plotly
- Streamlit
- pytest

## RFM Methodology

| Metric | Description |
|---|---|
| Recency | Days since the customer's latest completed purchase |
| Frequency | Number of distinct completed invoices |
| Monetary | Total net amount spent on completed purchases |

Each metric receives a score from 1 to 5. The three scores are combined to assign customer segments.

## Dataset

This project uses a synthetic e-commerce dataset generated for academic and demonstration purposes. It does not contain actual customer records.

- 500 customers
- 80 products
- 10,291 raw transaction records
- 9,978 retained cleaned transaction records
- 313 quarantined records

**RFM reference date:** 01 November 2026  
**Currency:** Indian Rupees (INR)

## Key Findings

- 497 customers included in the RFM output.
- 7 customer segments identified.
- 127 customers classified as At Risk.
- 90 customers classified as Champions.
- Books was the highest-revenue product category.
- January 2026 was the highest-revenue month.

These findings are based on synthetic data.

## Project Structure

```text
CUSTOMER_SEGMENTATION_USING_RFM_ANALYSIS/
├── data/
├── database/
├── notebooks/
├── outputs/
├── scripts/
├── sql/
├── tests/
├── app.py
├── main.py
├── requirements.txt
└── README.md
```

## Installation and Execution

Clone the repository:

```bash
git clone https://github.com/priyanshuwork127/CUSTOMER_SEGMENTATION_USING_RFM_ANALYSIS.git
cd CUSTOMER_SEGMENTATION_USING_RFM_ANALYSIS
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run automated tests:

```bash
pytest -v
```

Launch the dashboard:

```bash
streamlit run app.py
```

## Testing

The project includes 16 automated test cases covering database structure, row counts, key integrity, RFM calculations, SQL output files and application syntax.

## Limitations

- Dataset is synthetic.
- The project performs descriptive RFM analysis, not predictive churn modelling.
- Results are illustrative and are not claims about real customers.

## Future Scope

- Complete additional business intelligence reporting.
- Add more dashboard interaction tests.
- Evaluate customer segments over multiple time periods.
- Explore predictive analytics as a separate extension.

## Author

**Priyanshu**  
ABES Engineering College — Batch 16  
Email: priyanshu.25b15410254@abes.ac.in

## GitHub Repository

https://github.com/priyanshuwork127/CUSTOMER_SEGMENTATION_USING_RFM_ANALYSIS.git

## References and Learning Resources

- Python: https://docs.python.org/3/
- Pandas: https://pandas.pydata.org/docs/
- SQLite: https://www.sqlite.org/docs.html
- Streamlit: https://docs.streamlit.io/
- Plotly: https://plotly.com/python/
- pytest: https://docs.pytest.org/
- ChatGPT (OpenAI): https://chatgpt.com/ — AI-assisted project planning, explanations, debugging guidance and documentation drafting.
