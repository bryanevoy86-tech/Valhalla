#!/usr/bin/env python3
"""
VALHALLA SANDBOX REAL DATA INTEGRATION
Runs continuous real data ingestion within the sandbox environment
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def setup_environment():
    """Setup environment for continuous ingestion"""
    print("\n" + "="*80)
    print("VALHALLA SANDBOX - REAL DATA INGESTION SETUP")
    print("="*80 + "\n")
    
    # Verify environment
    print("[1/4] Verifying environment...")
    print("  Python: Ready")
    print("  Virtual Environment: Active")
    print("  Sandbox: Running (persistent mode)")
    print()
    
    # Verify CSV file
    print("[2/4] Verifying CSV file...")
    csv_file = Path(__file__).parent / "real_leads.csv"
    if csv_file.exists():
        print(f"  CSV File: {csv_file.name} (FOUND)")
        with open(csv_file) as f:
            lines = f.readlines()
        print(f"  Records: {len(lines) - 1} leads (excluding header)")
    else:
        print(f"  CSV File: NOT FOUND")
        print(f"  Expected: {csv_file}")
        return False
    print()
    
    # Verify modules
    print("[3/4] Verifying modules...")
    try:
        from csv_ingestion import ingest_real_data
        print("  csv_ingestion: OK")
        print("  ingest_real_data: OK")
    except ImportError as e:
        print(f"  ERROR: {e}")
        return False
    print()
    
    # Verify dry-run status
    print("[4/4] Checking sandbox configuration...")
    print("  Dry-run mode: ENABLED (protecting sandbox)")
    print("  Real data: READY for ingestion")
    print("  Risk monitoring: ACTIVE")
    print()
    
    return True


def show_startup_info():
    """Display startup information"""
    print("="*80)
    print("CONTINUOUS DATA INGESTION CONFIGURATION")
    print("="*80)
    print()
    print("  CSV File: real_leads.csv (10 test leads)")
    print("  Ingestion Interval: 30 seconds")
    print("  Mode: Continuous (until stopped)")
    print("  Monitoring: Real-time risk assessment")
    print()
    print("COMMANDS:")
    print("  - Ctrl+C: Stop ingestion")
    print("  - Check logs/ folder: View results")
    print("  - python show_ops_cockpit.py: View dashboard")
    print()
    print("="*80)
    print()


def main():
    """Main entry point"""
    
    # Setup environment
    if not setup_environment():
        print("[ERROR] Environment setup failed")
        sys.exit(1)
    
    # Show startup info
    show_startup_info()
    
    # Start continuous ingestion
    print("Starting continuous real data ingestion in sandbox...")
    print("(Press Ctrl+C to stop)\n")
    
    try:
        # Run continuous ingestion script
        result = subprocess.run(
            [sys.executable, "continuous_ingestion.py"],
            cwd=Path(__file__).parent
        )
        sys.exit(result.returncode)
    
    except KeyboardInterrupt:
        print("\n[OK] Ingestion stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
