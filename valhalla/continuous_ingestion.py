#!/usr/bin/env python3
"""
VALHALLA CONTINUOUS DATA INGESTION - SANDBOX INTEGRATION
Real data ingestion running continuously in sandbox environment
"""

import time
import sys
from pathlib import Path
from datetime import datetime
from csv_ingestion import ingest_real_data
import json

class ContinuousDataIngestion:
    """Manages continuous real data ingestion in sandbox"""
    
    def __init__(self, csv_path: str, interval: int = 30):
        """
        Initialize continuous ingestion
        
        Args:
            csv_path: Path to CSV file with real data
            interval: Seconds between ingestion cycles (default: 30)
        """
        self.csv_path = Path(csv_path)
        self.interval = interval
        self.cycle_count = 0
        self.total_leads_ingested = 0
        self.total_leads_valid = 0
        self.start_time = None
        self.stats = {
            "start_time": None,
            "cycles_completed": 0,
            "total_leads": 0,
            "valid_leads": 0,
            "invalid_leads": 0,
            "last_cycle_time": None,
            "status": "INITIALIZING"
        }
    
    def log_status(self, message: str):
        """Log status message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def run_ingestion_cycle(self) -> bool:
        """
        Run single data ingestion cycle
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.cycle_count += 1
        cycle_start = datetime.now()
        
        self.log_status(f"[CYCLE {self.cycle_count}] Starting ingestion cycle...")
        
        try:
            # Check if file exists
            if not self.csv_path.exists():
                self.log_status(f"[ERROR] CSV file not found: {self.csv_path}")
                return False
            
            # Ingest real data
            leads = ingest_real_data(str(self.csv_path))
            
            if leads:
                self.total_leads_ingested += len(leads)
                self.total_leads_valid += len(leads)
                self.stats["total_leads"] += len(leads)
                self.stats["valid_leads"] += len(leads)
                
                cycle_time = (datetime.now() - cycle_start).total_seconds()
                self.stats["last_cycle_time"] = cycle_time
                
                self.log_status(f"[OK] Cycle {self.cycle_count} complete: "
                              f"{len(leads)} leads ingested in {cycle_time:.2f}s")
                return True
            else:
                self.log_status(f"[WARNING] Cycle {self.cycle_count}: No leads ingested")
                return False
        
        except Exception as e:
            self.log_status(f"[ERROR] Cycle {self.cycle_count} failed: {str(e)}")
            return False
    
    def save_stats(self):
        """Save ingestion statistics to JSON"""
        stats_path = Path("logs/continuous_ingestion_stats.json")
        stats_path.parent.mkdir(exist_ok=True)
        
        self.stats["last_update"] = datetime.now().isoformat()
        self.stats["cycles_completed"] = self.cycle_count
        
        with open(stats_path, "w") as f:
            json.dump(self.stats, f, indent=2)
    
    def run_continuous(self, max_cycles: int = None):
        """
        Run continuous data ingestion loop
        
        Args:
            max_cycles: Maximum cycles to run (None = infinite)
        """
        self.start_time = datetime.now()
        self.stats["start_time"] = self.start_time.isoformat()
        self.stats["status"] = "RUNNING"
        
        self.log_status("="*80)
        self.log_status("CONTINUOUS DATA INGESTION - SANDBOX MODE")
        self.log_status("="*80)
        self.log_status(f"CSV Path: {self.csv_path}")
        self.log_status(f"Interval: {self.interval} seconds")
        self.log_status(f"Max Cycles: {max_cycles if max_cycles else 'INFINITE'}")
        self.log_status("="*80 + "\n")
        
        try:
            while True:
                # Check max cycles
                if max_cycles and self.cycle_count >= max_cycles:
                    self.log_status(f"Max cycles ({max_cycles}) reached. Stopping.")
                    break
                
                # Run ingestion cycle
                self.run_ingestion_cycle()
                
                # Save stats
                self.save_stats()
                
                # Show statistics
                self.show_stats()
                
                # Wait for next cycle
                if max_cycles is None or self.cycle_count < max_cycles:
                    self.log_status(f"Waiting {self.interval}s before next cycle...\n")
                    time.sleep(self.interval)
        
        except KeyboardInterrupt:
            self.log_status("\n" + "="*80)
            self.log_status("INGESTION STOPPED BY USER")
            self.log_status("="*80)
        
        finally:
            self.stats["status"] = "STOPPED"
            self.save_stats()
            self.show_final_report()
    
    def show_stats(self):
        """Display current statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        
        print(f"\n  Statistics:")
        print(f"    Cycles completed: {self.cycle_count}")
        print(f"    Total leads ingested: {self.total_leads_ingested}")
        print(f"    Valid leads: {self.total_leads_valid}")
        print(f"    Uptime: {hours}h {minutes}m {seconds}s")
        print()
    
    def show_final_report(self):
        """Display final ingestion report"""
        if not self.start_time:
            return
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        avg_per_cycle = self.total_leads_ingested / self.cycle_count if self.cycle_count > 0 else 0
        
        print("\n" + "="*80)
        print("CONTINUOUS INGESTION FINAL REPORT")
        print("="*80)
        print(f"  Total Cycles: {self.cycle_count}")
        print(f"  Total Leads Ingested: {self.total_leads_ingested}")
        print(f"  Valid Leads: {self.total_leads_valid}")
        print(f"  Average Leads/Cycle: {avg_per_cycle:.1f}")
        print(f"  Total Uptime: {uptime:.1f}s")
        print(f"  Status: {self.stats['status']}")
        print(f"  Report: logs/continuous_ingestion_stats.json")
        print("="*80 + "\n")


def main():
    """Main entry point"""
    
    # CSV file path - UPDATE THIS TO YOUR REAL DATA PATH
    csv_path = Path(__file__).parent / "real_leads.csv"
    
    # Create continuous ingestion instance
    ingestion = ContinuousDataIngestion(
        csv_path=str(csv_path),
        interval=30  # Ingest every 30 seconds
    )
    
    # Run continuous ingestion (unlimited cycles)
    # To limit cycles: ingestion.run_continuous(max_cycles=10)
    ingestion.run_continuous()


if __name__ == "__main__":
    main()
