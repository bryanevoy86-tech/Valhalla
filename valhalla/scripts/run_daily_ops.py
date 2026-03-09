"""
Daily Ops Email Runner

Run the daily ops email sender.

Usage:
    python scripts/run_daily_ops.py

This script:
1. Imports the daily ops job
2. Executes the run() function
3. Sends daily ops email to the system inbox

Can be scheduled via:
- Render cron job
- APScheduler in app
- Manual trigger
- GitHub Actions
"""

import sys
import os

# Add services/api to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'api'))

from app.jobs.daily_ops_email import run

if __name__ == "__main__":
    run()
