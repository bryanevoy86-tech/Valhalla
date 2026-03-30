#!/usr/bin/env python3
"""
TASK 2: Log the actual SQL being executed for GET /api/deals
This shows the exact query SQLAlchemy generates
"""
import os
import sys
import logging

# Setup SQL logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Add the services/api directory to the path
sys.path.insert(0, 'services/api')

# Now import the app components
from app.core.db import SessionLocal
from app.deals.models import Deal
from app.deals.schemas import DealOut

def main():
    print('='*70)
    print('TASK 2: EXACT SQL FOR GET /api/deals')
    print('='*70)
    
    db = SessionLocal()
    
    try:
        print('\n🔍 Executing: db.query(Deal).offset(0).limit(100).all()')
        print('Expected to see SQL below:\n')
        
        # This is what get_all_deals does
        result = db.query(Deal).offset(0).limit(100).all()
        
        print(f'\n✅ Query executed successfully')
        print(f'Result: {len(result)} deals returned\n')
        
        if result:
            print('First deal:')
            deal = result[0]
            print(f'  - id: {deal.id}')
            print(f'  - title: {deal.title}')
            print(f'  - created_ts: {getattr(deal, "created_ts", "MISSING")}')
            print(f'  - updated_ts: {getattr(deal, "updated_ts", "MISSING")}')
            print(f'  - created_at: {getattr(deal, "created_at", "NOT FOUND")}')
            print(f'  - updated_at: {getattr(deal, "updated_at", "NOT FOUND")}')
            
    except Exception as e:
        print(f'\n❌ Error: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print('\n' + '='*70)
    print('Check log output above for SQL statement')
    print('='*70)

if __name__ == '__main__':
    main()
