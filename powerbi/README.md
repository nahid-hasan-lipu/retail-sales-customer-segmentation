# Power BI Dashboard

A second, parallel dashboard built in Power BI Desktop alongside the Python/Streamlit app, to demonstrate BI-tool proficiency on the same dataset.

![Executive Overview](screenshots/executive_overview.png)
![Customer Segmentation Detail](screenshots/segmentation_detail.png)

## Data model

Two tables imported from `data/processed/`, plus a standard calculated date dimension:

- **Transactions** — the cleaned transaction-level fact table
- **CustomerSegments** — the RFM output (one row per customer)
- **DateTable** — a calculated date dimension (`CALENDAR()`), related on a date-only key to avoid the time-of-day component on `InvoiceDate` breaking the join

Relationships: `Transactions[Customer_ID]` → `CustomerSegments[Customer_ID]`, and `Transactions[InvoiceDateOnly]` → `DateTable[Date]` (both many-to-one, single-direction).

## DAX measures

```dax
Total Revenue = SUMX(FILTER(Transactions, Transactions[is_cancellation] = FALSE), Transactions[Revenue])

Total Orders = CALCULATE(DISTINCTCOUNT(Transactions[Invoice]), Transactions[is_cancellation] = FALSE)

Total Customers = CALCULATE(DISTINCTCOUNT(Transactions[Customer_ID]), Transactions[is_cancellation] = FALSE)

Avg Order Value = DIVIDE([Total Revenue], [Total Orders])

Champions Revenue Share = 
DIVIDE(
    CALCULATE([Total Revenue], CustomerSegments[Segment] = "Champions"),
    [Total Revenue]
)
```

All revenue-based measures explicitly exclude cancelled orders (`is_cancellation = FALSE`), so they reconcile exactly with the Python analysis in the main README.

## Report pages

**Executive Overview** — 4 KPI cards (revenue, orders, customers, AOV), monthly revenue trend, revenue by segment, customer count by segment (donut), and slicers for country/segment/year.

**Customer Segmentation Detail** — RFM summary table by segment, a Frequency-vs-Monetary scatter plot sized by recency, and a top-10-products-by-revenue chart.

## Reproducing this report

1. Run `python src/clean_data.py` and `python src/analysis.py` from the project root to generate the source CSVs.
2. In Power BI Desktop: Get Data → Text/CSV → import `data/processed/transactions_clean.csv` and `data/processed/rfm_segments.csv`.
3. Build the date table, relationships, and measures as specified above.
4. Recreate the visuals per the Report pages description.

The `.pbix` file itself isn't committed (binary format, doesn't diff or preview on GitHub) — the screenshots above are the source of truth for what the finished report looks like.
