"""Interactive Streamlit dashboard for the Retail Sales & Customer Segmentation project.

Run with: streamlit run dashboard/app.py
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"

st.set_page_config(page_title="Retail Sales & Customer Segmentation", layout="wide",
                    page_icon="🛍️")


@st.cache_data
def load_data():
    txns = pd.read_csv(DATA / "transactions_clean.csv", parse_dates=["InvoiceDate"])
    rfm = pd.read_csv(DATA / "rfm_segments.csv")
    trend = pd.read_csv(DATA / "monthly_trend.csv")
    return txns, rfm, trend


txns, rfm, trend = load_data()

st.title("🛍️ Retail Sales & Customer Segmentation")
st.caption("Online Retail II — UK-based online gift retailer, Dec 2009 – Dec 2011 "
           "(794K transactions, 5,895 customers, 41 countries)")

# ------------------------------------------------------------- Sidebar ----
st.sidebar.header("Filters")
countries = ["All"] + sorted(txns["Country"].unique().tolist())
country_sel = st.sidebar.selectbox("Country", countries)
segments = ["All"] + sorted(rfm["Segment"].unique().tolist())
segment_sel = st.sidebar.selectbox("Customer segment", segments)

sales = txns[~txns["is_cancellation"]].copy()
if country_sel != "All":
    sales = sales[sales["Country"] == country_sel]
if segment_sel != "All":
    seg_customers = rfm.loc[rfm["Segment"] == segment_sel, "Customer_ID"]
    sales = sales[sales["Customer_ID"].isin(seg_customers)]

# --------------------------------------------------------------- KPIs -----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"£{sales['Revenue'].sum():,.0f}")
c2.metric("Orders", f"{sales['Invoice'].nunique():,}")
c3.metric("Customers", f"{sales['Customer_ID'].nunique():,}")
aov = sales.groupby("Invoice")["Revenue"].sum().mean()
c4.metric("Avg. order value", f"£{aov:,.2f}")

st.divider()

# ---------------------------------------------------------- Trend chart ---
left, right = st.columns([2, 1])
with left:
    st.subheader("Monthly Revenue Trend")
    monthly = sales.groupby("InvoiceYearMonth").agg(
        Revenue=("Revenue", "sum"), Orders=("Invoice", "nunique")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly["InvoiceYearMonth"], y=monthly["Revenue"],
                              mode="lines+markers", name="Revenue", line=dict(color="#2563eb")))
    fig.update_layout(height=380, yaxis_title="Revenue (£)", xaxis_title=None,
                       margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width='stretch')

with right:
    st.subheader("Revenue by Segment")
    seg_rev = rfm.groupby("Segment")["Monetary"].sum().sort_values(ascending=False)
    fig2 = px.bar(seg_rev, orientation="h", color=seg_rev.values,
                   color_continuous_scale="Blues")
    fig2.update_layout(height=380, showlegend=False, coloraxis_showscale=False,
                        xaxis_title="Revenue (£)", yaxis_title=None,
                        margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig2, width='stretch')

st.divider()

# --------------------------------------------------------- RFM explorer ---
st.subheader("RFM Segment Explorer")
seg_summary = rfm.groupby("Segment").agg(
    Customers=("Customer_ID", "count"),
    Avg_Recency_Days=("Recency", "mean"),
    Avg_Frequency=("Frequency", "mean"),
    Avg_Monetary=("Monetary", "mean"),
    Total_Revenue=("Monetary", "sum"),
).round(1).sort_values("Total_Revenue", ascending=False)
st.dataframe(seg_summary, width='stretch')

fig3 = px.scatter(rfm, x="Frequency", y="Monetary", color="Segment", size="Recency",
                   hover_data=["Customer_ID"], log_y=True,
                   title="Customer Distribution: Frequency vs Monetary Value")
fig3.update_layout(height=450)
st.plotly_chart(fig3, width='stretch')

st.divider()

# ------------------------------------------------------ Top products -----
st.subheader("Top Products & Countries")
p1, p2 = st.columns(2)
with p1:
    top_products = sales.groupby("Description")["Revenue"].sum().sort_values(
        ascending=False).head(10).sort_values()
    fig4 = px.bar(top_products, orientation="h")
    fig4.update_layout(height=350, showlegend=False, xaxis_title="Revenue (£)",
                        yaxis_title=None, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig4, width='stretch')
with p2:
    top_countries = sales[sales["Country"] != "United Kingdom"].groupby(
        "Country")["Revenue"].sum().sort_values(ascending=False).head(10).sort_values()
    fig5 = px.bar(top_countries, orientation="h", color_discrete_sequence=["#d97706"])
    fig5.update_layout(height=350, showlegend=False, xaxis_title="Revenue (£)",
                        yaxis_title=None, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig5, width='stretch')

st.caption("Data: UCI Online Retail II. Built by Nahid Hasan Lipu — "
           "[GitHub](https://github.com/nahid-hasan-lipu) · "
           "[LinkedIn](https://www.linkedin.com/in/nahid-hasan-lipu-922447355/)")
