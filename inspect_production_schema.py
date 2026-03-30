#!/usr/bin/env python3
"""
SURGICAL DIAGNOSIS: Inspect production database schema
Task 1: Get actual columns in deals and leads tables
"""
import os
import sys
import psycopg2

def main():
    db_url = os.getenv('DATABASE_URL', '')
    
    if not db_url:
        print('⚠️  DATABASE_URL not set in environment')
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        db_url = line.split('=', 1)[1].strip()
                        break
        except:
            pass
    
    if not db_url:
        print('❌ Cannot find DATABASE_URL')
        print('Production DB inspection requires connection string')
        sys.exit(1)
    
    try:
        host = db_url.split('@')[1].split('/')[0] if '@' in db_url else 'unknown'
        print(f'🔗 Connecting to production DB: {host}')
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # TASK 1: Get deals table columns
        print('\n' + '='*70)
        print('TASK 1: DEALS TABLE ACTUAL SCHEMA')
        print('='*70)
        cursor.execute('''
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'deals'
            ORDER BY ordinal_position
        ''')
        columns = cursor.fetchall()
        if columns:
            print('\nColumn Name'.ljust(25), 'Data Type'.ljust(25), 'Nullable')
            print('-' * 70)
            for col_name, data_type, nullable in columns:
                nullable_str = 'YES' if nullable == 'YES' else 'NO'
                print(col_name.ljust(25), data_type.ljust(25), nullable_str)
            print(f'\n✅ deals table has {len(columns)} columns')
        else:
            print('❌ No deals table found in production DB')
        
        # TASK 1B: Get leads table columns
        print('\n' + '='*70)
        print('TASK 1B: LEADS TABLE ACTUAL SCHEMA')
        print('='*70)
        cursor.execute('''
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'leads'
            ORDER BY ordinal_position
        ''')
        columns = cursor.fetchall()
        if columns:
            print('\nColumn Name'.ljust(25), 'Data Type'.ljust(25), 'Nullable')
            print('-' * 70)
            for col_name, data_type, nullable in columns:
                nullable_str = 'YES' if nullable == 'YES' else 'NO'
                print(col_name.ljust(25), data_type.ljust(25), nullable_str)
            print(f'\n✅ leads table has {len(columns)} columns')
        else:
            print('❌ No leads table found in production DB')
        
        cursor.close()
        conn.close()
        print('\n' + '='*70)
        print('✅ Schema inspection complete')
        print('='*70)
        
    except Exception as e:
        print(f'\n❌ Error: {type(e).__name__}: {e}')
        if 'psycopg2' in str(type(e)):
            print('\nNote: psycopg2 driver error - check DATABASE_URL validity')
        sys.exit(1)

if __name__ == '__main__':
    main()
