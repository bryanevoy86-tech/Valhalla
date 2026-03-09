"""QuickBooks chart of accounts."""

CHART_OF_ACCOUNTS = {
    "REVENUE": "4000",
    "COGS": "5000",
    "FEES": "5100",
    "PROFIT": "6000",
    "CASH": "1000",
    "ACCOUNTS_RECEIVABLE": "1200",
    "EQUIPMENT": "1500",
    "ACCUMULATED_DEPRECIATION": "1550",
    "ACCOUNTS_PAYABLE": "2000",
    "LOAN_PAYABLE": "2100",
    "CAPITAL": "3000",
    "RETAINED_EARNINGS": "3100",
}


def get_account_number(account_type):
    """Get account number by type."""
    return CHART_OF_ACCOUNTS.get(account_type)


def list_accounts():
    """List all chart of accounts."""
    return CHART_OF_ACCOUNTS
