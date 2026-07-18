"""Clean the raw Online Retail II workbook into a single processed transactions file.

Source: UCI Online Retail II (https://archive.ics.uci.edu/dataset/502/online+retail+ii)
Two sheets covering 01-Dec-2009 to 09-Dec-2011, UK-based online gift retailer.
"""
import pandas as pd
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "online_retail_II.xlsx"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "transactions_clean.csv"


def load_raw() -> pd.DataFrame:
    xls = pd.ExcelFile(RAW_PATH)
    frames = [pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names]
    df = pd.concat(frames, ignore_index=True)
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    n_start = len(df)

    # Cancellations: invoices prefixed with 'C'. Kept out of revenue analysis,
    # but flagged rather than dropped so refund rate can still be reported.
    df["Invoice"] = df["Invoice"].astype(str)
    df["is_cancellation"] = df["Invoice"].str.startswith("C")

    # Rows with no Customer ID can't be attributed to a customer for RFM/cohort
    # analysis, and StockCodes like 'POST', 'DOT', 'M', 'BANK CHARGES' are fees/
    # adjustments, not products.
    non_product_codes = {"POST", "DOT", "M", "BANK CHARGES", "PADS", "CRUK", "AMAZONFEE"}
    df = df[df["Customer_ID"].notna()]
    df = df[~df["StockCode"].astype(str).str.upper().isin(non_product_codes)]

    # Negative/zero quantity on non-cancellation rows and non-positive price
    # rows are data-entry artefacts, not real transactions.
    df = df[(df["Price"] > 0)]
    df = df[(df["is_cancellation"]) | (df["Quantity"] > 0)]

    df["Customer_ID"] = df["Customer_ID"].astype(int)
    df["Revenue"] = df["Quantity"] * df["Price"]
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["InvoiceYearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)

    df = df.drop_duplicates()

    print(f"Rows: {n_start:,} raw -> {len(df):,} clean "
          f"({(1 - len(df) / n_start):.1%} removed)")
    return df


def main():
    df = clean(load_raw())
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Saved: {OUT_PATH} ({len(df):,} rows)")
    print(f"Date range: {df['InvoiceDate'].min()} -> {df['InvoiceDate'].max()}")
    print(f"Customers: {df['Customer_ID'].nunique():,} | Countries: {df['Country'].nunique()}")
    print(f"Total revenue (excl. cancellations): "
          f"£{df.loc[~df['is_cancellation'], 'Revenue'].sum():,.0f}")


if __name__ == "__main__":
    main()
