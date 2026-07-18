"""Core analysis: RFM segmentation, monthly sales trend, cohort retention.

Writes result tables to data/processed/ and chart PNGs to figures/, so both
the Streamlit dashboard and the README can reuse the same numbers.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
FIGS = ROOT / "figures"
FIGS.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 120, "font.size": 10, "axes.spines.top": False,
                      "axes.spines.right": False})


def load_transactions() -> pd.DataFrame:
    df = pd.read_csv(DATA / "transactions_clean.csv", parse_dates=["InvoiceDate"])
    return df


# ---------------------------------------------------------------- RFM -----
def build_rfm(df: pd.DataFrame) -> pd.DataFrame:
    sales = df[~df["is_cancellation"]].copy()
    snapshot_date = sales["InvoiceDate"].max() + pd.Timedelta(days=1)

    rfm = sales.groupby("Customer_ID").agg(
        Recency=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
        Frequency=("Invoice", "nunique"),
        Monetary=("Revenue", "sum"),
    ).reset_index()

    # Quintile scores: 5 = best (most recent / most frequent / highest spend).
    rfm["R_Score"] = pd.qcut(rfm["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["Monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["RFM_Score"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]

    def segment(row):
        r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        if r >= 3 and f >= 3:
            return "Loyal Customers"
        if r >= 4 and f <= 2:
            return "New Customers"
        if r <= 2 and f >= 4:
            return "At Risk"
        if r <= 2 and f <= 2 and m <= 2:
            return "Lost"
        if r >= 3 and m >= 4:
            return "Big Spenders"
        return "Needs Attention"

    rfm["Segment"] = rfm.apply(segment, axis=1)
    rfm.to_csv(DATA / "rfm_segments.csv", index=False)
    return rfm


def plot_rfm(rfm: pd.DataFrame):
    seg_summary = (rfm.groupby("Segment").agg(Customers=("Customer_ID", "count"),
                                                Revenue=("Monetary", "sum"))
                   .sort_values("Revenue", ascending=False))
    seg_summary.to_csv(DATA / "segment_summary.csv")

    fig, ax = plt.subplots(figsize=(7, 4))
    seg_summary["Revenue"].plot(kind="bar", ax=ax, color="#2563eb")
    ax.set_ylabel("Revenue (£)")
    ax.set_xlabel("")
    ax.set_title("Revenue by Customer Segment (RFM)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x/1e6:.1f}M"))
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(FIGS / "revenue_by_segment.png")
    plt.close()

    fig, ax = plt.subplots(figsize=(6, 6))
    seg_summary["Customers"].plot(kind="pie", ax=ax, autopct="%1.0f%%", startangle=90,
                                   colors=plt.cm.Blues_r(np.linspace(0.3, 0.9, len(seg_summary))))
    ax.set_ylabel("")
    ax.set_title("Customer Count by Segment")
    plt.tight_layout()
    plt.savefig(FIGS / "customers_by_segment.png")
    plt.close()
    return seg_summary


# --------------------------------------------------------- Sales trend ----
def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    sales = df[~df["is_cancellation"]].copy()
    trend = sales.groupby("InvoiceYearMonth").agg(
        Revenue=("Revenue", "sum"),
        Orders=("Invoice", "nunique"),
        Customers=("Customer_ID", "nunique"),
    ).reset_index()
    # Drop the partial first/last calendar months so the trend line isn't
    # distorted by incomplete months at the edges of the dataset's date range.
    trend = trend.iloc[1:-1].reset_index(drop=True)
    trend.to_csv(DATA / "monthly_trend.csv", index=False)

    fig, ax1 = plt.subplots(figsize=(9, 4))
    ax1.plot(trend["InvoiceYearMonth"], trend["Revenue"], color="#2563eb", marker="o", ms=3)
    ax1.set_ylabel("Revenue (£)", color="#2563eb")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x/1e3:.0f}K"))
    ax1.set_title("Monthly Revenue Trend")
    plt.xticks(rotation=60, ha="right", fontsize=7)
    plt.tight_layout()
    plt.savefig(FIGS / "monthly_revenue_trend.png")
    plt.close()
    return trend


# ------------------------------------------------------------- Cohorts ----
def cohort_retention(df: pd.DataFrame) -> pd.DataFrame:
    sales = df[~df["is_cancellation"]].copy()
    sales["OrderMonth"] = sales["InvoiceDate"].dt.to_period("M")
    first_purchase = sales.groupby("Customer_ID")["OrderMonth"].min().rename("CohortMonth")
    sales = sales.join(first_purchase, on="Customer_ID")
    sales["CohortIndex"] = (sales["OrderMonth"] - sales["CohortMonth"]).apply(lambda p: p.n)

    cohort_counts = (sales.groupby(["CohortMonth", "CohortIndex"])["Customer_ID"]
                      .nunique().reset_index())
    cohort_pivot = cohort_counts.pivot(index="CohortMonth", columns="CohortIndex",
                                        values="Customer_ID")
    cohort_size = cohort_pivot.iloc[:, 0]
    retention = cohort_pivot.divide(cohort_size, axis=0)
    retention.to_csv(DATA / "cohort_retention.csv")

    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(retention.iloc[:, :12], cmap="Blues", vmin=0, vmax=0.6, aspect="auto")
    ax.set_xticks(range(12))
    ax.set_xticklabels(range(12))
    ax.set_yticks(range(len(retention)))
    ax.set_yticklabels([str(i) for i in retention.index])
    ax.set_xlabel("Months since first purchase")
    ax.set_ylabel("Acquisition cohort")
    ax.set_title("Monthly Customer Retention by Cohort")
    plt.colorbar(im, ax=ax, label="Retention rate")
    plt.tight_layout()
    plt.savefig(FIGS / "cohort_retention_heatmap.png")
    plt.close()
    return retention


# --------------------------------------------------------- Top products ---
def top_products_countries(df: pd.DataFrame):
    sales = df[~df["is_cancellation"]].copy()
    top_products = (sales.groupby("Description")["Revenue"].sum()
                     .sort_values(ascending=False).head(10))
    top_products.to_csv(DATA / "top_products.csv")

    top_countries = (sales[sales["Country"] != "United Kingdom"]
                      .groupby("Country")["Revenue"].sum()
                      .sort_values(ascending=False).head(10))
    top_countries.to_csv(DATA / "top_countries_ex_uk.csv")

    fig, ax = plt.subplots(figsize=(7, 4))
    top_products.sort_values().plot(kind="barh", ax=ax, color="#059669")
    ax.set_xlabel("Revenue (£)")
    ax.set_title("Top 10 Products by Revenue")
    plt.tight_layout()
    plt.savefig(FIGS / "top_products.png")
    plt.close()

    fig, ax = plt.subplots(figsize=(7, 4))
    top_countries.sort_values().plot(kind="barh", ax=ax, color="#d97706")
    ax.set_xlabel("Revenue (£)")
    ax.set_title("Top 10 Countries by Revenue (excl. UK)")
    plt.tight_layout()
    plt.savefig(FIGS / "top_countries.png")
    plt.close()


def main():
    df = load_transactions()
    rfm = build_rfm(df)
    seg_summary = plot_rfm(rfm)
    trend = monthly_trend(df)
    retention = cohort_retention(df)
    top_products_countries(df)

    print("=== Segment summary ===")
    print(seg_summary)
    print("\n=== Monthly trend (last 3 months) ===")
    print(trend.tail(3))
    print("\nAll outputs written to data/processed/ and figures/")


if __name__ == "__main__":
    main()
