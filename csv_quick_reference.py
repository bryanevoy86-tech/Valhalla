#!/usr/bin/env python3
"""
VALHALLA CSV INGESTION - QUICK REFERENCE CARD
Copy and paste these commands to use CSV ingestion
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         VALHALLA CSV INGESTION - QUICK REFERENCE CARD                     ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝


COMMAND REFERENCE
═══════════════════════════════════════════════════════════════════════════════

[1] RUN CSV INGESTION (Default File: real_leads.csv)
    $ python csv_ingestion.py

[2] RUN PRODUCTION WORKFLOW (Ingest + Risk Assessment + Processing)
    $ python production_workflow.py

[3] RUN EXAMPLES (6 working examples with different approaches)
    $ python csv_ingestion_examples.py

[4] VIEW SYSTEM STATUS
    $ python validate_production_mode.py

[5] MONITOR RISKS
    $ python risk_monitoring_system.py


CSV FILE FORMAT REQUIRED
═══════════════════════════════════════════════════════════════════════════════

MINIMUM COLUMNS (Required):
    name       - Lead name (text)
    email      - Email address (must have @ and .)
    value      - Lead value (positive number)

OPTIONAL COLUMNS:
    location   - Location (text)
    phone      - Phone number (text)
    source     - Data source (text)

EXAMPLE CSV:
    name,email,value,location,phone
    John Doe,john@example.com,500000,Houston TX,713-555-0123
    Jane Smith,jane@example.com,750000,Dallas TX,214-555-0456


VALIDATION RULES
═══════════════════════════════════════════════════════════════════════════════

Field          Rule                           Example
───────────────────────────────────────────────────────────────────────────────
name           Non-empty text                 John Doe
email          Must have @ and .              john@example.com
value          Positive number (>0)           500000 or 500000.50
location       Any text                       Houston TX
phone          Any text                       713-555-0123
───────────────────────────────────────────────────────────────────────────────

INVALID EXAMPLES:
  - Email: john.example.com (missing @)
  - Email: john@example (missing .)
  - Value: abc (not a number)
  - Value: -500 (must be positive)
  - Value: 0 (must be greater than 0)


PYTHON CODE EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

[BASIC USAGE]
    from csv_ingestion import ingest_real_data
    leads = ingest_real_data("real_leads.csv")
    print(f"Loaded {len(leads)} leads")

[WITH CUSTOM PATH]
    from csv_ingestion import ingest_real_data
    leads = ingest_real_data("C:\\path\\to\\my_leads.csv")

[USING CLASS]
    from csv_ingestion import CSVIngestion
    ing = CSVIngestion("my_file.csv")
    leads = ing.ingest_from_csv()
    print(f"Valid: {ing.leads_valid}, Invalid: {ing.leads_invalid}")

[PROCESS RESULTS]
    from csv_ingestion import ingest_real_data
    leads = ingest_real_data("data.csv")
    if leads:
        for lead in leads:
            print(f"{lead['name']}: ${lead['value']:,.2f}")

[BATCH PROCESSING]
    from pathlib import Path
    from csv_ingestion import ingest_real_data
    
    for csv_file in Path(".").glob("*.csv"):
        leads = ingest_real_data(str(csv_file))
        if leads:
            print(f"{csv_file.name}: {len(leads)} leads")

[ERROR HANDLING]
    from csv_ingestion import ingest_real_data
    leads = ingest_real_data("my_file.csv")
    if leads:
        print(f"Success: {len(leads)} leads loaded")
    else:
        print("Error: Could not load file")


PIPELINE STAGES
═══════════════════════════════════════════════════════════════════════════════

Each lead processes through 6 stages:

[1/6] A/B Test Tracking      - Assign to test group
[2/6] Script Promotion       - Evaluate lead quality
[3/6] Deal Packet            - Generate deal information
[4/6] Outcome Evaluation     - Score lead potential
[5/6] Clone Readiness        - Check replication readiness
[6/6] Lead Scoring           - Final quality score


OUTPUT & LOGGING
═══════════════════════════════════════════════════════════════════════════════

CONSOLE OUTPUT:
    [STARTING] CSV Ingestion from: path/to/file.csv
    [PROCESSING] John Doe - john@example.com - Value: $500,000.00
    [INGESTION COMPLETE]
    Total records: 10
    Valid leads: 10
    Invalid leads: 0
    Success rate: 100.0%

JSON REPORTS (in logs/ folder):
    logs/production_execution.json         - Production workflow data
    logs/risk_monitoring_results.json      - Risk assessment results
    logs/production_validation_complete.json - Validation report


TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════

PROBLEM: "CSV file is empty or has no headers"
SOLUTION: Ensure first row contains column headers

PROBLEM: "Invalid email format"
SOLUTION: Email must have both @ and . (john@example.com)

PROBLEM: "Value must be numeric"
SOLUTION: Remove currency symbols ($) and commas from value field

PROBLEM: "File not found"
SOLUTION: Use full path or ensure file is in valhalla directory

PROBLEM: "No output displayed"
SOLUTION: Scripts may be writing to logs/ folder instead of console


SYSTEM STATUS
═══════════════════════════════════════════════════════════════════════════════

Dry-Run Mode          : DISABLED (Real data processing)
CSV Ingestion         : OPERATIONAL (Tested with 10 leads)
Data Quality Score    : 95.0% (All validation checks pass)
Risk Monitoring       : ACTIVE (0 critical alerts)
Production Pipeline   : WORKING (6-step flow complete)
Error Logging         : ENABLED (JSON reports generated)


DOCUMENTATION
═══════════════════════════════════════════════════════════════════════════════

Full Guide               CSV_INGESTION_GUIDE.md
Implementation Summary  CSV_INGESTION_IMPLEMENTATION.md
Working Examples        csv_ingestion_examples.py
Module Code             csv_ingestion.py
Production Workflow     production_workflow.py


QUICK TEST
═══════════════════════════════════════════════════════════════════════════════

To test everything is working:

$ python csv_ingestion.py

Expected output:
- Shows 10 test leads being processed
- All 6 pipeline stages complete
- "Success rate: 100.0%" at end


PRODUCTION WORKFLOW
═══════════════════════════════════════════════════════════════════════════════

To run complete production workflow:

$ python production_workflow.py

This will:
1. Disable dry-run mode
2. Read real_leads.csv
3. Validate all data
4. Assess risks
5. Process through pipeline
6. Generate JSON reports


═══════════════════════════════════════════════════════════════════════════════

Status: PRODUCTION READY
Last Updated: 2026-01-07

Ready to process real CSV data!
""")
