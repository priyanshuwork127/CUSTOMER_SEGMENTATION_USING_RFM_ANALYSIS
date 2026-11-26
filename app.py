
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

# ==========================================
# 1. CONFIGURATION
# ==========================================

ROOT = Path(__file__).resolve().parent
SQL_RESULTS = ROOT / "outputs" / "sql_results"

st.set_page_config(
    page_title="RFM Customer Analytics",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# 2. LOAD DATA
# ==========================================

@st.cache_data
def load_rfm():
    path = SQL_RESULTS / "q1_customer_rfm_segments.csv"

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)

    required_columns = [
        "customer_id", "city", "state",
        "acquisition_channel", "recency_days",
        "frequency", "monetary", "r_score",
        "f_score", "m_score", "rfm_score",
        "customer_segment"
    ]

    missing = [c for c in required_columns if c not in df.columns]

    if missing:
        raise ValueError(f"Missing RFM columns: {missing}")

    return df


@st.cache_data
def load_optional_csv(filename):
    path = SQL_RESULTS / filename

    if path.exists():
        return pd.read_csv(path)

    return None


try:
    rfm = load_rfm()
except Exception as error:
    st.error(f"Unable to load RFM data: {error}")
    st.stop()


# ==========================================
# 3. DASHBOARD HEADER
# ==========================================

st.title("Customer Segmentation Dashboard")
st.caption(
    "E-commerce Analytics | RFM Analysis | "
    "Reference Date: 1 November 2026"
)

st.divider()


# ==========================================
# 4. SIDEBAR FILTERS
# ==========================================

st.sidebar.title("Dashboard Filters")

segments = sorted(rfm["customer_segment"].dropna().unique())
states = sorted(rfm["state"].dropna().unique())
channels = sorted(rfm["acquisition_channel"].dropna().unique())

selected_segments = st.sidebar.multiselect(
    "Customer Segment",
    segments,
    default=segments
)

selected_states = st.sidebar.multiselect(
    "State",
    states,
    default=states
)

selected_channels = st.sidebar.multiselect(
    "Acquisition Channel",
    channels,
    default=channels
)

filtered = rfm[
    rfm["customer_segment"].isin(selected_segments)
    & rfm["state"].isin(selected_states)
    & rfm["acquisition_channel"].isin(selected_channels)
].copy()


# ==========================================
# 5. HANDLE EMPTY FILTER RESULTS
# ==========================================

if filtered.empty:
    st.warning("No customers match the selected filters.")
    st.stop()


# ==========================================
# 6. KPI CALCULATIONS
# ==========================================

total_customers = filtered["customer_id"].nunique()

total_revenue = filtered["monetary"].sum()

avg_frequency = filtered["frequency"].mean()

avg_recency = filtered["recency_days"].mean()

avg_monetary = filtered["monetary"].mean()


# ==========================================
# 7. KPI CARDS
# ==========================================

st.subheader("Business Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Total Customers",
    f"{total_customers:,}"
)

c2.metric(
    "Total Monetary Value",
    f"₹{total_revenue:,.0f}"
)

c3.metric(
    "Average Frequency",
    f"{avg_frequency:.1f}"
)

c4.metric(
    "Average Recency",
    f"{avg_recency:.1f} days"
)

c5, c6 = st.columns(2)

c5.metric(
    "Average Customer Monetary",
    f"₹{avg_monetary:,.0f}"
)

c6.metric(
    "Customer Segments",
    filtered["customer_segment"].nunique()
)

st.divider()


# ==========================================
# 8. CUSTOMER SEGMENT DISTRIBUTION
# ==========================================

st.subheader("Customer Segment Analysis")

segment_counts = (
    filtered.groupby("customer_segment")["customer_id"]
    .nunique()
    .reset_index(name="customer_count")
)

col1, col2 = st.columns(2)

with col1:

    fig = px.bar(
        segment_counts,
        x="customer_segment",
        y="customer_count",
        color="customer_segment",
        text="customer_count",
        title="Customers by Segment",
        labels={
            "customer_segment": "Customer Segment",
            "customer_count": "Number of Customers"
        }
    )

    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


with col2:

    fig = px.pie(
        segment_counts,
        names="customer_segment",
        values="customer_count",
        hole=0.45,
        title="Customer Segment Share"
    )

    st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 9. REVENUE BY CUSTOMER SEGMENT
# ==========================================

st.subheader("Revenue Contribution by Segment")

segment_revenue = (
    filtered.groupby("customer_segment")["monetary"]
    .sum()
    .reset_index()
    .sort_values("monetary", ascending=False)
)

fig = px.bar(
    segment_revenue,
    x="customer_segment",
    y="monetary",
    color="customer_segment",
    text_auto=".2s",
    title="Monetary Contribution by Customer Segment",
    labels={
        "customer_segment": "Customer Segment",
        "monetary": "Monetary Value (INR)"
    }
)

fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 10. RECENCY, FREQUENCY, MONETARY
# ==========================================

st.subheader("RFM Behaviour Analysis")

col1, col2 = st.columns(2)

with col1:

    fig = px.histogram(
        filtered,
        x="recency_days",
        nbins=25,
        title="Customer Recency Distribution",
        labels={"recency_days": "Recency (Days)"}
    )

    st.plotly_chart(fig, use_container_width=True)


with col2:

    fig = px.histogram(
        filtered,
        x="frequency",
        nbins=25,
        title="Customer Frequency Distribution",
        labels={"frequency": "Number of Purchases"}
    )

    st.plotly_chart(fig, use_container_width=True)


fig = px.histogram(
    filtered,
    x="monetary",
    color="customer_segment",
    nbins=30,
    title="Customer Monetary Value Distribution",
    labels={"monetary": "Monetary Value (INR)"}
)

st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 11. RFM SCORE ANALYSIS
# ==========================================

st.subheader("RFM Score Comparison")

score_data = (
    filtered.groupby("customer_segment")
    [["r_score", "f_score", "m_score"]]
    .mean()
    .reset_index()
)

score_long = score_data.melt(
    id_vars="customer_segment",
    var_name="RFM Component",
    value_name="Average Score"
)

score_long["RFM Component"] = (
    score_long["RFM Component"]
    .map({
        "r_score": "Recency Score",
        "f_score": "Frequency Score",
        "m_score": "Monetary Score"
    })
)

fig = px.bar(
    score_long,
    x="customer_segment",
    y="Average Score",
    color="RFM Component",
    barmode="group",
    title="Average RFM Scores by Customer Segment"
)

st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 12. ACQUISITION CHANNEL ANALYSIS
# ==========================================

st.subheader("Acquisition Channel Analysis")

channel_data = (
    filtered.groupby("acquisition_channel")
    .agg(
        customers=("customer_id", "nunique"),
        revenue=("monetary", "sum")
    )
    .reset_index()
)

col1, col2 = st.columns(2)

with col1:

    fig = px.bar(
        channel_data,
        x="acquisition_channel",
        y="customers",
        color="acquisition_channel",
        title="Customers by Acquisition Channel"
    )

    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


with col2:

    fig = px.bar(
        channel_data,
        x="acquisition_channel",
        y="revenue",
        color="acquisition_channel",
        title="Monetary Value by Acquisition Channel"
    )

    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 13. STATE ANALYSIS
# ==========================================

st.subheader("Geographical Customer Analysis")

state_data = (
    filtered.groupby("state")
    .agg(
        customers=("customer_id", "nunique"),
        revenue=("monetary", "sum")
    )
    .reset_index()
    .sort_values("revenue", ascending=False)
)

fig = px.bar(
    state_data,
    x="state",
    y="revenue",
    color="customers",
    title="Revenue by State",
    labels={
        "state": "State",
        "revenue": "Monetary Value (INR)",
        "customers": "Customers"
    }
)

st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 14. OPTIONAL SQL RESULT CHARTS
# ==========================================

def display_sql_chart(filename, title):

    data = load_optional_csv(filename)

    if data is None or data.empty:
        st.info(f"{filename} is not available.")
        return

    numeric_columns = data.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = data.select_dtypes(
        exclude="number"
    ).columns.tolist()

    if not numeric_columns or not categorical_columns:
        st.info(f"Could not identify chart columns in {filename}.")
        return

    preferred = [
        c for c in numeric_columns
        if any(word in c.lower()
               for word in ["revenue", "amount", "sales", "net"])
    ]

    y_column = preferred[0] if preferred else numeric_columns[0]
    x_column = categorical_columns[0]

    fig = px.bar(
        data,
        x=x_column,
        y=y_column,
        title=title
    )

    st.plotly_chart(fig, use_container_width=True)


st.subheader("Additional SQL Analysis")

col1, col2 = st.columns(2)

with col1:
    display_sql_chart(
        "q4_revenue_by_product_category.csv",
        "Revenue by Product Category"
    )

with col2:
    display_sql_chart(
        "q5_monthly_revenue.csv",
        "Monthly Revenue Trend"
    )


# ==========================================
# 15. TOP 10 CUSTOMERS
# ==========================================

st.subheader("Top 10 Customers by Monetary Value")

top_customers = (
    filtered.sort_values("monetary", ascending=False)
    .head(10)
    [[
        "customer_id",
        "city",
        "state",
        "customer_segment",
        "recency_days",
        "frequency",
        "monetary",
        "rfm_score"
    ]]
)

st.dataframe(
    top_customers,
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 16. COMPLETE CUSTOMER TABLE
# ==========================================

st.subheader("Customer Details")

st.dataframe(
    filtered.sort_values("monetary", ascending=False),
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 17. DOWNLOAD FILTERED DATA
# ==========================================

csv_data = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Customer Data",
    data=csv_data,
    file_name="filtered_rfm_customers.csv",
    mime="text/csv"
)


# ==========================================
# 18. FOOTER
# ==========================================

st.divider()

st.caption(
    "Customer Segmentation Using RFM Analysis | "
    "Academic Project | Synthetic E-commerce Dataset"
)

st.caption(
    "Monetary values represent completed-order spending "
    "as calculated in the SQL analysis."
)
