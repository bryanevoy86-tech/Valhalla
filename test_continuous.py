
from continuous_ingestion import ContinuousDataIngestion
from pathlib import Path

csv_path = Path(__file__).parent / "real_leads.csv"
ingestion = ContinuousDataIngestion(str(csv_path), interval=1)
ingestion.run_continuous(max_cycles=3)
