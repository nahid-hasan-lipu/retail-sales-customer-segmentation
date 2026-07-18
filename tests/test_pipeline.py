"""Sanity checks for the cleaning and analysis pipeline.

Run with: pytest tests/
"""
import pandas as pd
import pytest
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "processed"


@pytest.fixture(scope="module")
def transactions():
    path = DATA / "transactions_clean.csv"
    if not path.exists():
        pytest.skip("Run src/clean_data.py first to generate processed data.")
    return pd.read_csv(path, parse_dates=["InvoiceDate"])


@pytest.fixture(scope="module")
def rfm():
    path = DATA / "rfm_segments.csv"
    if not path.exists():
        pytest.skip("Run src/analysis.py first to generate RFM segments.")
    return pd.read_csv(path)


def test_no_missing_customer_ids(transactions):
    assert transactions["Customer_ID"].notna().all()


def test_no_non_positive_prices(transactions):
    assert (transactions["Price"] > 0).all()


def test_revenue_equals_quantity_times_price(transactions):
    expected = transactions["Quantity"] * transactions["Price"]
    assert (transactions["Revenue"] - expected).abs().max() < 1e-6


def test_non_cancellation_quantities_are_positive(transactions):
    sales = transactions[~transactions["is_cancellation"]]
    assert (sales["Quantity"] > 0).all()


def test_rfm_scores_in_valid_range(rfm):
    for col in ["R_Score", "F_Score", "M_Score"]:
        assert rfm[col].between(1, 5).all()


def test_rfm_segments_are_known_categories(rfm):
    expected_segments = {"Champions", "Loyal Customers", "New Customers", "At Risk",
                          "Lost", "Big Spenders", "Needs Attention"}
    assert set(rfm["Segment"].unique()) <= expected_segments


def test_every_customer_has_exactly_one_segment(rfm):
    assert rfm["Customer_ID"].is_unique
