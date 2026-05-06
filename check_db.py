import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
print(f"DATABASE_URL env: {db_url}")

try:
    from services.api.app.core.db import engine
    print(f"Engine URL: {engine.url}")
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(conn.exec("SELECT 1"))
        print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Error: {e}")
