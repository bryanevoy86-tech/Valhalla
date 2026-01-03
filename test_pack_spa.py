import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from app.core_gov.credit import credit_router
from app.core_gov.pantheon import pantheon_router
from app.core_gov.analytics import analytics_router
print("✅ All routers imported successfully")
print("✅ P-CREDIT-1, P-PANTHEON-1, P-ANALYTICS-1 modules ready")
