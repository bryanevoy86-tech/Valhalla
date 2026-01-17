#!/usr/bin/env python3
"""
VALHALLA DATA INGESTION MODULE
Handles CSV ingestion and real data processing with validation
"""

import csv
import logging
import json
from pathlib import Path
from datetime import datetime

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DATA_INGESTION - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "data_ingestion.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataValidator:
    """Validate lead data before ingestion"""
    
    REQUIRED_FIELDS = ["name", "email", "value"]
    
    @staticmethod
    def validate_lead(lead):
        """
        Validate that lead data meets criteria
        
        Returns: (is_valid, error_message)
        """
        # Check required fields
        missing_fields = [f for f in DataValidator.REQUIRED_FIELDS if not lead.get(f)]
        if missing_fields:
            return False, f"Missing required fields: {missing_fields}"
        
        # Validate email format
        email = lead.get("email", "").lower().strip()
        if "@" not in email or "." not in email:
            return False, f"Invalid email format: {email}"
        
        # Validate value is positive number
        try:
            value = float(lead.get("value", 0))
            if value <= 0:
                return False, f"Invalid value (must be > 0): {value}"
        except (ValueError, TypeError):
            return False, f"Value must be numeric: {lead.get('value')}"
        
        # Validate name is not empty
        name = lead.get("name", "").strip()
        if not name or len(name) < 2:
            return False, f"Invalid name (too short): {name}"
        
        return True, None
    
    @staticmethod
    def sanitize_lead(lead):
        """Clean and standardize lead data"""
        return {
            "name": lead.get("name", "").strip().title(),
            "email": lead.get("email", "").lower().strip(),
            "value": float(lead.get("value", 0)),
            "location": lead.get("location", "").strip(),
            "phone": lead.get("phone", "").strip(),
            "source": lead.get("source", "CSV_IMPORT"),
            "ingestion_date": datetime.now().isoformat()
        }


class CSVDataIngestion:
    """Handle CSV file ingestion"""
    
    def __init__(self):
        self.ingested_count = 0
        self.valid_count = 0
        self.invalid_count = 0
        self.ingested_leads = []
    
    def ingest_from_csv(self, file_path):
        """
        Ingest leads from a CSV file
        
        CSV Format expected:
        name, email, value, [location], [phone], [source]
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        logger.info(f"Starting CSV ingestion from: {file_path}")
        
        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                    self.ingested_count += 1
                    
                    # Validate lead
                    is_valid, error = DataValidator.validate_lead(row)
                    
                    if not is_valid:
                        self.invalid_count += 1
                        logger.warning(f"Row {row_num}: Invalid lead data - {error}")
                        continue
                    
                    # Sanitize lead
                    clean_lead = DataValidator.sanitize_lead(row)
                    self.ingested_leads.append(clean_lead)
                    self.valid_count += 1
                    
                    logger.info(f"Row {row_num}: ✓ Valid lead - {clean_lead['name']} ({clean_lead['email']})")
            
            # Log summary
            logger.info(f"\n=== CSV INGESTION SUMMARY ===")
            logger.info(f"Total rows processed: {self.ingested_count}")
            logger.info(f"Valid leads: {self.valid_count}")
            logger.info(f"Invalid leads: {self.invalid_count}")
            logger.info(f"Success rate: {(self.valid_count/max(self.ingested_count, 1))*100:.1f}%")
            
            return True
            
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return False
    
    def get_ingested_leads(self):
        """Return all valid ingested leads"""
        return self.ingested_leads
    
    def export_results(self, output_file="ingestion_results.json"):
        """Export ingestion results to JSON"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_rows": self.ingested_count,
                "valid_leads": self.valid_count,
                "invalid_leads": self.invalid_count,
                "success_rate": f"{(self.valid_count/max(self.ingested_count, 1))*100:.1f}%"
            },
            "leads": self.ingested_leads
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results exported to: {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    print("\n=== DATA INGESTION MODULE ===\n")
    
    ingestion = CSVDataIngestion()
    
    # Check if test CSV exists
    test_csv = "real_leads.csv"
    if Path(test_csv).exists():
        success = ingestion.ingest_from_csv(test_csv)
        if success:
            print(f"\nIngested {ingestion.valid_count} valid leads")
            ingestion.export_results()
    else:
        print(f"Test file '{test_csv}' not found.")
        print("Create a CSV file with columns: name, email, value, [location], [phone]")
