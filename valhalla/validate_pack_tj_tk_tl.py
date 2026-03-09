#!/usr/bin/env python3
"""
Validation script for PACK TJ, TK, TL completion.
Verifies migration file and existing application components.
"""

import os
import sys

def validate_migration_file():
    """Verify migration file 0066_pack_tj_tk_tl.py exists and is valid."""
    migration_path = "services/api/alembic/versions/0066_pack_tj_tk_tl.py"
    
    if not os.path.exists(migration_path):
        print(f"❌ Migration file not found: {migration_path}")
        return False
    
    with open(migration_path, 'r') as f:
        content = f.read()
        required_tables = [
            'child_profiles',
            'learning_plans',
            'education_logs',
            'life_events',
            'life_milestones',
            'strategic_decisions',
            'decision_revisions'
        ]
        
        for table in required_tables:
            if f"'{table}'" not in content:
                print(f"❌ Missing table in migration: {table}")
                return False
    
    print(f"✅ Migration file valid: {migration_path}")
    return True


def validate_routers():
    """Verify router files exist."""
    routers = [
        "services/api/app/routers/kids_education.py",
        # Note: life_timeline and strategic_decision are in /routes not /routers
        "services/api/app/routes/life_timeline.py",
        "services/api/app/routes/strategic_decision.py"
    ]
    
    all_exist = True
    for router in routers:
        if os.path.exists(router):
            print(f"✅ Router exists: {router}")
        else:
            print(f"❌ Router missing: {router}")
            all_exist = False
    
    return all_exist


def validate_models():
    """Verify model files exist."""
    models = [
        "services/api/app/models/kids_education.py",
        "services/api/app/models/life_timeline.py",
        "services/api/app/models/strategic_decision.py"
    ]
    
    all_exist = True
    for model in models:
        if os.path.exists(model):
            print(f"✅ Model exists: {model}")
        else:
            print(f"❌ Model missing: {model}")
            all_exist = False
    
    return all_exist


def validate_schemas():
    """Verify schema files exist."""
    schemas = [
        "services/api/app/schemas/kids_education.py",
        "services/api/app/schemas/life_timeline.py",
        "services/api/app/schemas/strategic_decision.py"
    ]
    
    all_exist = True
    for schema in schemas:
        if os.path.exists(schema):
            print(f"✅ Schema exists: {schema}")
        else:
            print(f"❌ Schema missing: {schema}")
            all_exist = False
    
    return all_exist


def main():
    """Run all validations."""
    print("=" * 60)
    print("PACK TJ, TK, TL Validation")
    print("=" * 60)
    
    print("\n📋 Checking Migration Files...")
    migration_ok = validate_migration_file()
    
    print("\n🔀 Checking Routers...")
    routers_ok = validate_routers()
    
    print("\n📦 Checking Models...")
    models_ok = validate_models()
    
    print("\n📋 Checking Schemas...")
    schemas_ok = validate_schemas()
    
    print("\n" + "=" * 60)
    if migration_ok and routers_ok and models_ok and schemas_ok:
        print("✅ ALL VALIDATIONS PASSED")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
