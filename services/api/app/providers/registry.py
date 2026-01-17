from app.providers.plaid_adapter import PlaidAdapter
from app.providers.stripe_adapter import StripeAdapter
from app.providers.docusign_adapter import DocusignAdapter

ADAPTERS = {
    "plaid": PlaidAdapter(),
    "stripe": StripeAdapter(),
    "docusign": DocusignAdapter(),
}
