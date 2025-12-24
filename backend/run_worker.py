"""
Worker runner helper script.

Run with: python backend/run_worker.py
"""

from app.core.workers.runner import run_forever

if __name__ == "__main__":
    run_forever()
