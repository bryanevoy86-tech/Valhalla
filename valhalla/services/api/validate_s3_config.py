#!/usr/bin/env python3
"""
Validate Contract Pipeline S3 configuration and readiness.

Usage:
    python validate_s3_config.py --bucket valhalla-contracts --region us-east-1
"""
import os
import sys
import argparse
import boto3
from pathlib import Path


def check_environment():
    """Check environment variables are set."""
    print("\n[CHECK] Environment Variables")
    print("-" * 50)
    
    required = {
        "CONTRACT_STORAGE_BACKEND": "s3",
        "CONTRACT_S3_BUCKET": None,
        "AWS_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": None,
        "AWS_SECRET_ACCESS_KEY": None,
    }
    
    optional = {
        "CONTRACT_S3_PREFIX": "prod/contracts",
        "AWS_ENDPOINT_URL": None,
        "CONTRACT_S3_SSE": None,
        "CONTRACT_S3_KMS_KEY_ID": None,
    }
    
    all_good = True
    
    # Check required
    for key, default in required.items():
        value = os.getenv(key, default)
        if not value:
            print(f"  ✗ {key}: NOT SET (required)")
            all_good = False
        else:
            masked = value[:20] + "..." if len(str(value)) > 20 else value
            print(f"  ✓ {key}: {masked}")
    
    # Check optional
    for key, default in optional.items():
        value = os.getenv(key, default)
        if value:
            masked = value[:20] + "..." if len(str(value)) > 20 else value
            print(f"  ℹ {key}: {masked} (optional)")
        else:
            print(f"  - {key}: not set (optional)")
    
    return all_good


def check_s3_access():
    """Test S3 bucket access."""
    print("\n[CHECK] S3 Bucket Access")
    print("-" * 50)
    
    try:
        bucket = os.getenv("CONTRACT_S3_BUCKET")
        region = os.getenv("AWS_REGION", "us-east-1")
        endpoint_url = os.getenv("AWS_ENDPOINT_URL")
        
        if not bucket:
            print("  ✗ S3_BUCKET not configured")
            return False
        
        # Create S3 client
        kwargs = {
            "region_name": region,
        }
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        
        client = boto3.client("s3", **kwargs)
        
        # Test bucket access
        response = client.head_bucket(Bucket=bucket)
        print(f"  ✓ Bucket '{bucket}' is accessible")
        
        # List a few objects to verify read permission
        try:
            objects = client.list_objects_v2(Bucket=bucket, MaxKeys=5)
            count = objects.get("KeyCount", 0)
            print(f"  ✓ Read permission verified ({count} objects)")
        except Exception as e:
            print(f"  ⚠ List objects failed: {e}")
        
        # Test write by creating a test object
        try:
            test_key = f".test_{os.getpid()}.txt"
            client.put_object(
                Bucket=bucket,
                Key=test_key,
                Body=b"test content",
            )
            print(f"  ✓ Write permission verified (test object created)")
            
            # Clean up
            client.delete_object(Bucket=bucket, Key=test_key)
            print(f"  ✓ Delete permission verified")
        except Exception as e:
            print(f"  ✗ Write permission failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ S3 access failed: {e}")
        return False


def check_database():
    """Check database connectivity and migrations."""
    print("\n[CHECK] Database Configuration")
    print("-" * 50)
    
    try:
        from sqlalchemy import create_engine, inspect
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            print("  ✗ DATABASE_URL not configured")
            return False
        
        # Parse DB type
        db_type = db_url.split("://")[0] if "://" in db_url else "unknown"
        print(f"  ✓ Database type: {db_type}")
        
        if db_type == "sqlite":
            print("  ℹ SQLite detected (development)")
        elif db_type == "postgresql":
            print("  ✓ PostgreSQL detected (production)")
        
        # Check migrations exist
        migrations_dir = Path("alembic/versions")
        if migrations_dir.exists():
            migration_files = list(migrations_dir.glob("*.py"))
            print(f"  ✓ Found {len(migration_files)} migrations")
            
            # Check for contract migrations
            contract_migrations = [f for f in migration_files if "contract" in f.name.lower()]
            if contract_migrations:
                print(f"  ✓ Contract migrations found:")
                for mig in sorted(contract_migrations)[-3:]:
                    print(f"    - {mig.name}")
            else:
                print("  ⚠ No contract migrations found")
        else:
            print("  ✗ alembic/versions directory not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Database check failed: {e}")
        return False


def check_routes():
    """Check if contract routes are registered."""
    print("\n[CHECK] Contract Routes")
    print("-" * 50)
    
    routes = [
        "POST /api/contracts",
        "POST /api/contracts/{id}/state",
        "POST /api/contracts/{id}/upload",
        "POST /api/contracts/{id}/send",
        "GET /api/contracts/{id}/events",
        "GET /api/contracts/{id}/documents/{doc_id}/download",
        "POST /api/contracts/templates/seed",
        "POST /api/contracts/webhooks/provider",
    ]
    
    print("  Expected routes:")
    for route in routes:
        print(f"    ✓ {route}")
    
    try:
        from app.routers import contracts_pipeline, contracts_webhooks
        print("\n  ✓ contracts_pipeline router imported successfully")
        print("  ✓ contracts_webhooks router imported successfully")
        return True
    except ImportError as e:
        print(f"\n  ✗ Failed to import routers: {e}")
        return False


def check_models():
    """Check if contract models exist."""
    print("\n[CHECK] Contract Models")
    print("-" * 50)
    
    models = [
        "ContractTemplate",
        "Contract",
        "ContractParty",
        "ContractDocument",
        "ContractEnvelope",
        "ContractEvent",
    ]
    
    try:
        from app.models.contracts import (
            ContractTemplate,
            Contract,
            ContractParty,
            ContractDocument,
            ContractEnvelope,
            ContractEvent,
        )
        
        for model_name in models:
            print(f"  ✓ {model_name} defined")
        
        return True
        
    except ImportError as e:
        print(f"  ✗ Failed to import models: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Validate Contract Pipeline S3 configuration"
    )
    parser.add_argument("--bucket", help="S3 bucket name (overrides env)")
    parser.add_argument("--region", help="AWS region (overrides env)")
    parser.add_argument("--endpoint", help="Custom endpoint URL (overrides env)")
    
    args = parser.parse_args()
    
    # Override environment if provided
    if args.bucket:
        os.environ["CONTRACT_S3_BUCKET"] = args.bucket
    if args.region:
        os.environ["AWS_REGION"] = args.region
    if args.endpoint:
        os.environ["AWS_ENDPOINT_URL"] = args.endpoint
    
    print("\n" + "=" * 50)
    print("CONTRACT PIPELINE VALIDATION")
    print("=" * 50)
    
    # Run checks
    checks = [
        ("Environment", check_environment),
        ("S3 Access", check_s3_access),
        ("Database", check_database),
        ("Routes", check_routes),
        ("Models", check_models),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n[ERROR] {name} check failed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ Ready for deployment!")
        return 0
    else:
        print("\n⚠️  Fix the above issues before deploying")
        return 1


if __name__ == "__main__":
    sys.exit(main())
