
from graphviz import Digraph
import os

# ==========================================
# 1. CREATE GRAPH
# ==========================================

dot = Digraph("RFM_Star_Schema", engine="twopi", format="png")

dot.attr(
    "graph",
    root="FACT",
    bgcolor="white",
    label="CUSTOMER SEGMENTATION USING RFM ANALYSIS\nSTAR SCHEMA",
    labelloc="t",
    fontsize="22",
    fontname="Arial",
    pad="0.7",
    ranksep="2.5",
    overlap="false"
)

dot.attr(
    "node",
    shape="plain",
    fontname="Arial"
)

dot.attr(
    "edge",
    color="#34495E",
    penwidth="1.8",
    arrowhead="none",
    fontname="Arial",
    fontsize="11"
)


# ==========================================
# 2. FUNCTION TO CREATE TABLES
# ==========================================

def create_table(title, header_color, body_color, fields):

    rows = ""

    for field in fields:
        rows += f"""
        <TR>
            <TD ALIGN="LEFT" CELLPADDING="7">
                {field}
            </TD>
        </TR>
        """

    # IMPORTANT: HTML label starts with <<TABLE and ends with </TABLE>>
    return f"""<
    <TABLE BORDER="1"
           CELLBORDER="0"
           CELLSPACING="0"
           CELLPADDING="5"
           BGCOLOR="{body_color}">

        <TR>
            <TD BGCOLOR="{header_color}" CELLPADDING="10">
                <FONT COLOR="white" POINT-SIZE="13">
                    <B>{title}</B>
                </FONT>
            </TD>
        </TR>

        {rows}

    </TABLE>
    >"""


# ==========================================
# 3. FACT TABLE - CENTRE
# ==========================================

dot.node(
    "FACT",
    label=create_table(
        "FACT_TRANSACTIONS",
        "#2874A6",
        "#DCEEFF",
        [
            "<B>PK</B> transaction_key",
            "<B>FK</B> customer_key",
            "<B>FK</B> product_key",
            "<B>FK</B> date_key",
            "<B>FK</B> payment_key",
            "<B>FK</B> status_key",
            "invoice_id",
            "quantity",
            "unit_price",
            "discount_pct",
            "gross_amount",
            "discount_amount",
            "net_amount"
        ]
    )
)


# ==========================================
# 4. CUSTOMER DIMENSION
# ==========================================

dot.node(
    "CUSTOMER",
    label=create_table(
        "DIM_CUSTOMER",
        "#148F77",
        "#E8F8F5",
        [
            "<B>PK</B> customer_key",
            "customer_id",
            "signup_date",
            "city",
            "state",
            "acquisition_channel"
        ]
    )
)


# ==========================================
# 5. PRODUCT DIMENSION
# ==========================================

dot.node(
    "PRODUCT",
    label=create_table(
        "DIM_PRODUCT",
        "#CA6F1E",
        "#FEF5E7",
        [
            "<B>PK</B> product_key",
            "product_id",
            "product_name",
            "category",
            "standard_unit_price"
        ]
    )
)


# ==========================================
# 6. DATE DIMENSION
# ==========================================

dot.node(
    "DATE",
    label=create_table(
        "DIM_DATE",
        "#7D3C98",
        "#F4ECF7",
        [
            "<B>PK</B> date_key",
            "full_date",
            "calendar_year",
            "quarter_number",
            "month_number",
            "month_name",
            "day_of_month",
            "day_name"
        ]
    )
)


# ==========================================
# 7. PAYMENT DIMENSION
# ==========================================

dot.node(
    "PAYMENT",
    label=create_table(
        "DIM_PAYMENT",
        "#C0392B",
        "#FDEDEC",
        [
            "<B>PK</B> payment_key",
            "payment_method"
        ]
    )
)


# ==========================================
# 8. ORDER STATUS DIMENSION
# ==========================================

dot.node(
    "STATUS",
    label=create_table(
        "DIM_ORDER_STATUS",
        "#566573",
        "#EAECEE",
        [
            "<B>PK</B> status_key",
            "order_status"
        ]
    )
)


# ==========================================
# 9. RELATIONSHIPS
# ==========================================

dot.edge("CUSTOMER", "FACT", label="1 : Many")
dot.edge("PRODUCT", "FACT", label="1 : Many")
dot.edge("DATE", "FACT", label="1 : Many")
dot.edge("PAYMENT", "FACT", label="1 : Many")
dot.edge("STATUS", "FACT", label="1 : Many")


# ==========================================
# 10. EXPORT IMAGE
# ==========================================

project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

output_path = os.path.join(
    project_folder,
    "RFM_Star_Schema"
)

output_file = dot.render(
    filename=output_path,
    cleanup=True,
    view=True
)

print("\nStar Schema generated successfully!")
print("Saved at:", output_file)
