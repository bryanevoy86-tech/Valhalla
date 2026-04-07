"""QuickBooks sync service."""
from app.integrations.quickbooks.client import post_journal_entry
from app.integrations.quickbooks.chart import CHART_OF_ACCOUNTS


def sync_revenue(amount):
    """Sync revenue entry to QuickBooks."""
    entry = {
        "account": CHART_OF_ACCOUNTS["REVENUE"],
        "amount": amount,
        "type": "revenue"
    }
    return post_journal_entry(entry)


def sync_fees(amount):
    """Sync fees entry to QuickBooks."""
    entry = {
        "account": CHART_OF_ACCOUNTS["FEES"],
        "amount": amount,
        "type": "expense"
    }
    return post_journal_entry(entry)


def sync_profit(amount):
    """Sync profit entry to QuickBooks."""
    entry = {
        "account": CHART_OF_ACCOUNTS["PROFIT"],
        "amount": amount,
        "type": "profit"
    }
    return post_journal_entry(entry)
