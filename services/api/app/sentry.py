import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from app.core.settings import settings

def setup_sentry(app):
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn)
        app.add_middleware(SentryAsgiMiddleware)
