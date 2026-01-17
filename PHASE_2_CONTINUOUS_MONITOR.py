#!/usr/bin/env python3
"""
PHASE 2 Continuous Monitor
===========================
Automatically runs Phase 2 simulation every 60 seconds to consume latest sandbox exports.
This ensures we're always analyzing the most recent lead data.
"""

import subprocess
import time
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PHASE_2_MONITOR - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_phase2():
    """Execute PHASE_2_SIMULATION.py and capture output."""
    try:
        result = subprocess.run(
            ["python", "PHASE_2_SIMULATION.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    logger.info("PHASE 2 CONTINUOUS MONITOR STARTED")
    logger.info("Running Phase 2 simulation every 60 seconds...")
    logger.info("Press Ctrl+C to stop.\n")
    
    cycle = 0
    while True:
        try:
            cycle += 1
            logger.info(f"[CYCLE {cycle}] Running Phase 2 simulation...")
            
            success, stdout, stderr = run_phase2()
            
            if success:
                # Extract key metrics from output
                if "PHASE 2 COMPLETE" in stdout:
                    lines = stdout.strip().split('\n')
                    for line in lines:
                        if "Source:" in line or "Report:" in line or "CSV:" in line:
                            logger.info(f"  → {line.strip()}")
                else:
                    logger.warning(f"  Phase 2 output unexpected (no COMPLETE marker)")
            else:
                logger.error(f"  Phase 2 failed: {stderr[:200] if stderr else 'unknown error'}")
            
            # Wait before next cycle
            logger.info(f"  Waiting 60s for next cycle...\n")
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("\nPhase 2 monitoring stopped.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in cycle {cycle}: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
