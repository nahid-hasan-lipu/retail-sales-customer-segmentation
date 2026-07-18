# Power BI Build Spec — Retail Sales & Customer Segmentation

Follow this in order inside Power BI Desktop. Data is already cleaned — this is
report authoring only. Every step says exactly which button/menu to click.

## Screen layout, so the instructions make sense

Down the **far-left edge** of the window you'll see 3 small icons stacked vertically:
- **Report view** (bar-chart icon) — where you build pages/visuals. This is the default view.
- **Table/Data view** (grid icon) — see raw data as a spreadsheet.
- **Model view** (diagram icon) — see tables and relationships between them.

At the **top** is the ribbon (tabs: File, Home, Insert, Modeling, View, Help). On the **right side** of Report view you'll see two stacked panes: **Visualizations** (chart type icons + formatting) above, **Fields** (your tables and columns, as a tree list) below.

---

## 1. Get data (2 tables)

1. Make sure you're on the **Home** tab of the ribbon (top-left, should already be selected).
2. Click the **Get Data** button — it's the large icon on the far-left of the Home ribbon, with a dropdown arrow underneath it.
3. A window titled "Get Data" opens with a search box and a list of data source types. Type `Text/CSV` into the search box, click **Text/CSV** from the results, then click **Connect** (bottom-right of the window).
4. A file browser opens. Navigate to and select:
   `Job Profile\Projects\retail-sales-customer-segmentation\data\processed\transactions_clean.csv`
   Click **Open**.
5. A preview window pops up showing the first rows of the file, with a **Load** button and a **Transform Data** button at the bottom-right. **Click "Transform Data"** (not Load) — this is important, it opens the Power Query Editor so we can fix things before the data loads into your report.

### You're now in Power Query Editor (a separate window/mode)

6. On the **left side**, there's a narrow "Queries" pane with one entry, probably named `transactions_clean`. **Double-click that name** and rename it to `Transactions`, then press Enter.
7. Look at the column headers in the main grid. Each header has a small icon just left of the column name showing its data type — e.g. `ABC` for text, `123` for whole number, a little calendar for Date, a calendar-with-clock for Date/Time.
8. Find the **InvoiceDate** column header. Look at its type icon:
   - **If it already shows a calendar-with-clock icon** (Date/Time) — it auto-detected correctly, skip to step 9.
   - **If it shows anything else** (e.g. `ABC` text, or just a calendar with no clock): click the small type icon itself (left of the column name) — a dropdown list appears with options like Text, Whole Number, Decimal Number, Date, Time, **Date/Time**. Click **Date/Time**.
   - A small popup may appear asking "Change Column Type — Replace current conversion?" with two buttons, **Replace Current** and **Add New Step**. Click **Replace Current**.
9. Repeat the same "Get Data → Text/CSV" process (steps 1-5) for the second file:
   `data\processed\rfm_segments.csv`
   When you reach the rename step, rename this query to `CustomerSegments`.
10. When both tables look right, click **Close & Apply** — this is a large button on the **far-left of the Home tab in Power Query Editor** (top-left corner). A progress dialog appears briefly, then you're dropped back into the normal Power BI Desktop report canvas, with both tables now visible in the **Fields** pane on the right.

---

## 2. Create a Date table

A "Date table" lets you group revenue by month/year cleanly — this is standard practice in every real Power BI report, not optional polish.

1. Go to the **Modeling** tab in the ribbon (top).
2. Click **New Table** (in the "Calculations" group).
3. A formula bar appears at the top of the canvas. Type exactly:
   ```
   DateTable = CALENDAR(MIN(Transactions[InvoiceDate]), MAX(Transactions[InvoiceDate]))
   ```
   Press **Enter**. A new table called `DateTable` now appears in the Fields pane on the right, with one column called `Date`.
4. With `DateTable` selected in the Fields pane (click on it once), go to **Modeling → New Column**. Type:
   ```
   Year = YEAR(DateTable[Date])
   ```
   Press Enter.
5. Click **New Column** again (still with DateTable selected). Type:
   ```
   MonthName = FORMAT(DateTable[Date], "MMM YYYY")
   ```
   Press Enter.
6. Click **New Column** once more. Type:
   ```
   MonthNum = YEAR(DateTable[Date])*100 + MONTH(DateTable[Date])
   ```
   Press Enter.
7. Now we need `MonthName` (e.g. "Mar 2010") to sort chronologically instead of alphabetically. Click on the **MonthName** column in the Fields pane (under DateTable) to select it. A new ribbon tab appears at the top called **Column tools** — click it. In that tab, find the **Sort by Column** dropdown (in the "Sort" group) and select **MonthNum**.
8. **Important — add a date-only join key.** `Transactions[InvoiceDate]` is Date/*Time* (it includes the time each order was placed), but `DateTable[Date]` is a plain Date with no time component. Relating a Date/Time column directly to a Date column matches **zero rows** (they're never exactly equal), which makes any chart using DateTable show blank. Fix it now, before building relationships: with **Transactions** selected in the Fields pane, go to **Modeling → New Column** and paste:
   ```
   InvoiceDateOnly = DATEVALUE(Transactions[InvoiceDate])
   ```
   Press Enter. We'll relate `DateTable[Date]` to this column instead of the raw `InvoiceDate` in the next section.

---

## 3. Relationships (linking the tables together)

1. Go to the **Modeling** tab → click **Manage Relationships**.
2. A dialog opens, probably showing that Power BI already auto-detected some relationships. Click **New** (or **Autodetect** if offered, then check the results) to add any missing ones. You need exactly these two:
   - `Transactions[Customer_ID]` ↔ `CustomerSegments[Customer_ID]` — Cardinality: **Many to one**, Cross filter direction: **Single**
   - `Transactions[InvoiceDateOnly]` ↔ `DateTable[Date]` — Cardinality: **Many to one**, Cross filter direction: **Single** — use `InvoiceDateOnly` (the column from step 8 above), **not** the raw `InvoiceDate` column, or every date-based chart will show blank.
3. If you use **New**: a small dialog lets you pick Table 1 + column, Table 2 + column, from dropdowns — pick the pairs above, leave Cardinality/Cross-filter on their auto-detected defaults (they should already read "Many to one" / "Single"), then click **OK**.
4. Click **Close** on the Manage Relationships dialog.

*(Tip: you can also see this visually — go to the small diagram icon on the far-left edge of the window (Model view) to see the tables as boxes with lines connecting them. If a line is missing, that's the relationship to add.)*

---

## 4. DAX measures (typed formulas that calculate KPIs)

1. In the **Fields** pane, click on the **Transactions** table name once to select it (single click, not the arrow to expand it).
2. Go to **Modeling → New Measure**. A formula bar appears at the top.
3. Type the formula below exactly, then press Enter. Repeat "Modeling → New Measure" for each one — do this 5 times, once per formula:

```dax
Total Revenue = SUMX(FILTER(Transactions, Transactions[is_cancellation] = FALSE), Transactions[Revenue])
```
```dax
Total Orders = CALCULATE(DISTINCTCOUNT(Transactions[Invoice]), Transactions[is_cancellation] = FALSE)
```
```dax
Total Customers = CALCULATE(DISTINCTCOUNT(Transactions[Customer_ID]), Transactions[is_cancellation] = FALSE)
```
```dax
Avg Order Value = DIVIDE([Total Revenue], [Total Orders])
```
```dax
Champions Revenue Share = 
DIVIDE(
    CALCULATE([Total Revenue], CustomerSegments[Segment] = "Champions"),
    [Total Revenue]
)
```

After typing each formula and pressing Enter, the new measure appears in the Fields pane under the Transactions table with a small calculator icon next to it — that's how you know it saved correctly.

---

## 5. Building the visuals

General pattern for every visual below: click an empty area of the canvas first (so nothing is selected), then in the **Visualizations** pane (top-right), click the icon for the chart type you want — this places an empty chart box on the canvas. With that box still selected, go to the **Fields** pane (bottom-right) and either **drag** a field onto the chart box, or **tick its checkbox** — both work the same way.

### Page 1 — Executive Overview
*(Rename the page: double-click the "Page 1" tab at the very bottom of the screen, type "Executive Overview")*

- **4 KPI cards** (top row): In Visualizations pane, click the **Card** icon (shows a single big number) four separate times to place 4 card boxes side by side. Drag one measure into each: `Total Revenue`, `Total Orders`, `Total Customers`, `Avg Order Value` (all four live under the Transactions table in the Fields pane).
- **Line chart** (monthly trend): Click the **Line chart** icon. Drag `DateTable[MonthName]` into the **X-axis** field well, and `Total Revenue` (the measure) into the **Y-axis** field well. There are ~25 months of data, so by default the chart may only show the first dozen or so with a thin horizontal scrollbar at the bottom rather than all of them at once — this is just a width limit, not missing data. Drag the chart's bottom-right corner to make it wider until the scrollbar disappears and every month is visible.
- **Bar chart** (revenue by segment): Click the **Clustered bar chart** icon. Drag `CustomerSegments[Segment]` into the **Y-axis** field well, and `CustomerSegments[Monetary]` into the **X-axis** field well. It should auto-sum and show as "Sum of Monetary" — but Power BI sometimes defaults numeric fields to **Count** instead. Check the field pill in the X-axis well: if it reads "Count of Monetary", click its dropdown arrow and change it to **Sum**. There are 7 segments, which may not all fit in the box at first (a vertical scrollbar appears) — drag the chart's bottom edge down to make it taller until all 7 show without scrolling.
- **Donut chart** (customers by segment): Click the **Donut chart** icon. Drag `CustomerSegments[Segment]` into **Legend**, and `CustomerSegments[Customer_ID]` into **Values** — click the small dropdown arrow on the field once it's placed and change it from "Count" to **Count (Distinct)** if it isn't already.
- **Slicers** (filter buttons): Click the **Slicer** icon three separate times, placing three boxes. Drag one field into each: `Transactions[Country]`, `CustomerSegments[Segment]`, `DateTable[Year]`. The Segment slicer may show an extra **"(Blank)"** checkbox item — this is expected, not an error: a small number of customers (33, in this dataset) only ever cancelled orders and never completed a purchase, so they have no RFM segment. Leave it as-is (accurate), or right-click "(Blank)" in the slicer → **Exclude** if you'd rather hide it for a cleaner look.

### Page 2 — Customer Segmentation Detail
*(Click the `+` icon next to the page tabs at the bottom to add a new page, then rename it the same way as above)*

- **Table**: Click the **Table** icon in Visualizations. Drag in `CustomerSegments[Segment]`, `CustomerSegments[Recency]`, `CustomerSegments[Frequency]`, `CustomerSegments[Monetary]`, `CustomerSegments[Customer_ID]`. For Recency/Frequency/Monetary, click the dropdown arrow on each field in the field well and change the summarization to **Average**. For Customer_ID, change it to **Count (Distinct)**.
- **Scatter chart**: Click the **Scatter chart** icon (may be under "More visuals" if not shown directly). Drag `CustomerSegments[Frequency]` into **X-axis**, `CustomerSegments[Monetary]` into **Y-axis**, `CustomerSegments[Segment]` into **Legend**, and `CustomerSegments[Recency]` into **Size**. Power BI auto-titles this something clunky like "Count of Recency by Segment, Frequency and Monetary" — worth renaming: click the chart, open **Format visual** (paint-roller icon in Visualizations pane) → **Title** → change the title text to something cleaner, e.g. "RFM Segment Distribution: Frequency vs Monetary".
- **Top 10 products bar chart**: Click the **Clustered bar chart** icon. Drag `Transactions[Description]` into **Y-axis** and the **`Total Revenue` measure** (calculator icon, not the raw `Revenue` column) into **X-axis** — using the raw column instead of the measure includes cancellation rows (negative revenue) in the total, which quietly swaps 2 of the top 10 products for wrong ones. Then, with the chart selected, open the **Filters** pane (usually a tab next to Visualizations, or below it) — find "Description" under "Filters on this visual", click the dropdown that says "Filter type", choose **Top N**, set it to **Top 10**, and drag the **`Total Revenue` measure** (same one, not the raw column) into the "By value" box, then click **Apply filter**.

---

## 6. Export & link

1. **Save**: `Ctrl+S`, or File → Save. Save it as `powerbi/retail_sales_segmentation.pbix` inside the project folder (this file is gitignored — see note below, it won't be uploaded to GitHub).
2. **Screenshots**: On each page, use Windows' Snipping Tool (`Win+Shift+S`) to capture the whole report canvas, and save the images into `powerbi/screenshots/` as PNG (e.g. `executive_overview.png`, `segmentation_detail.png`).
3. **Optional — publish for a live link**: Home tab → **Publish** button (top-right area of the Home ribbon). This uploads the report to the Power BI cloud service and gives you a shareable URL. If you'd rather not set up a cloud workspace right now, the screenshots + this repo are already enough to show the work — you can always publish later.

**Why the `.pbix` isn't committed to git**: it's a binary format git can't diff meaningfully, and GitHub can't preview it inline — screenshots in the README give a recruiter the same information without requiring them to open Power BI Desktop themselves.

---

## General tip: visuals showing stale/wrong results

If a visual looks wrong right after you change something in the model (add a column, fix a relationship, edit a measure), try **Home → Refresh** before assuming it's a new bug — Power BI Desktop's visuals don't always redraw immediately after a model change.

## Stuck on something not covered here?

Tell me exactly which numbered step and what you're seeing on screen (or describe/paste an error message) and I'll walk you through that specific step in more detail.
