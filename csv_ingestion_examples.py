#!/usr/bin/env python3
"""
EXAMPLE: CSV INGESTION WITH YOUR OWN DATA
This script shows how to use the CSV ingestion module with custom files
"""

from pathlib import Path
from csv_ingestion import CSVIngestion, ingest_real_data


def example_1_basic_ingestion():
    """Example 1: Basic CSV ingestion with default file"""
    print("\n" + "="*80)
    print("EXAMPLE 1: BASIC CSV INGESTION")
    print("="*80 + "\n")
    
    # Default file in same directory
    csv_path = Path(__file__).parent / "real_leads.csv"
    leads = ingest_real_data(str(csv_path))
    
    if leads:
        print(f"\nSuccessfully loaded {len(leads)} leads")
        for lead in leads[:3]:  # Show first 3
            print(f"  - {lead['name']}: {lead['email']} (${lead['value']:,.2f})")
    else:
        print("Failed to load leads")


def example_2_custom_file():
    """Example 2: Ingestion with custom file path"""
    print("\n" + "="*80)
    print("EXAMPLE 2: CUSTOM FILE PATH")
    print("="*80 + "\n")
    
    # Using custom file path
    custom_path = "C:\\Users\\YourName\\Documents\\my_leads.csv"
    
    print(f"Attempting to load from: {custom_path}")
    leads = ingest_real_data(custom_path)
    
    if leads:
        print(f"Loaded {len(leads)} leads")
    else:
        print("File not found or error occurred")


def example_3_using_class():
    """Example 3: Using CSVIngestion class directly"""
    print("\n" + "="*80)
    print("EXAMPLE 3: USING CSVINGESTION CLASS")
    print("="*80 + "\n")
    
    # Create ingestion instance
    csv_path = Path(__file__).parent / "real_leads.csv"
    ingestion = CSVIngestion(str(csv_path))
    
    # Ingest and process
    leads = ingestion.ingest_from_csv()
    
    if leads:
        print(f"\n\nStatistics:")
        print(f"  Total ingested: {ingestion.leads_ingested}")
        print(f"  Valid leads: {ingestion.leads_valid}")
        print(f"  Invalid leads: {ingestion.leads_invalid}")
        print(f"  Success rate: {(ingestion.leads_valid/ingestion.leads_ingested*100):.1f}%")
        
        # Access processed leads
        print(f"\n\nProcessed Leads ({len(leads)} total):")
        for i, lead in enumerate(leads[:5], 1):
            print(f"  {i}. {lead['name']}")
            print(f"     Email: {lead['email']}")
            print(f"     Value: ${lead['value']:,.2f}")
            print(f"     Location: {lead.get('location', 'N/A')}")
            print()


def example_4_data_processing():
    """Example 4: Process ingested data"""
    print("\n" + "="*80)
    print("EXAMPLE 4: PROCESS INGESTED DATA")
    print("="*80 + "\n")
    
    csv_path = Path(__file__).parent / "real_leads.csv"
    leads = ingest_real_data(str(csv_path))
    
    if leads:
        # Filter by value
        high_value_leads = [l for l in leads if l['value'] >= 750000]
        print(f"\nHigh-value leads (>=$750k): {len(high_value_leads)}")
        for lead in high_value_leads:
            print(f"  - {lead['name']}: ${lead['value']:,.2f}")
        
        # Calculate statistics
        total_value = sum(l['value'] for l in leads)
        avg_value = total_value / len(leads)
        print(f"\nValue Statistics:")
        print(f"  Total: ${total_value:,.2f}")
        print(f"  Average: ${avg_value:,.2f}")
        print(f"  Count: {len(leads)} leads")


def example_5_batch_processing():
    """Example 5: Process multiple CSV files"""
    print("\n" + "="*80)
    print("EXAMPLE 5: BATCH PROCESSING MULTIPLE FILES")
    print("="*80 + "\n")
    
    csv_dir = Path("c:\\dev\\valhalla")
    all_leads = []
    
    # Find all CSV files
    csv_files = list(csv_dir.glob("*.csv"))
    
    print(f"Found {len(csv_files)} CSV files:\n")
    
    for csv_file in csv_files:
        print(f"Processing: {csv_file.name}")
        leads = ingest_real_data(str(csv_file))
        
        if leads:
            all_leads.extend(leads)
            print(f"  - Loaded {len(leads)} leads")
        else:
            print(f"  - Failed to load")
    
    print(f"\n\nBatch Results:")
    print(f"  Total files processed: {len(csv_files)}")
    print(f"  Total leads ingested: {len(all_leads)}")


def example_6_error_handling():
    """Example 6: Handle errors gracefully"""
    print("\n" + "="*80)
    print("EXAMPLE 6: ERROR HANDLING")
    print("="*80 + "\n")
    
    test_files = [
        "real_leads.csv",
        "nonexistent.csv",
        "C:\\invalid\\path\\file.csv"
    ]
    
    for file_path in test_files:
        print(f"\nTrying to load: {file_path}")
        leads = ingest_real_data(file_path)
        
        if leads:
            print(f"  SUCCESS: Loaded {len(leads)} leads")
        else:
            print(f"  FAILED: Could not load file")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("CSV INGESTION EXAMPLES")
    print("="*80)
    
    # Run examples
    example_1_basic_ingestion()
    example_3_using_class()
    example_4_data_processing()
    
    print("\n" + "="*80)
    print("EXAMPLES COMPLETE")
    print("="*80)
    print("\nOther examples available:")
    print("  - Example 2: Custom file paths")
    print("  - Example 5: Batch processing multiple files")
    print("  - Example 6: Error handling")
    print("\nUncomment in main() to run them\n")
