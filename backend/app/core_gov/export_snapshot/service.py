"""
P-EXPORTSNAP-1: Export snapshot service.

Walks backend/data for JSON files and creates a snapshot export.
"""
import json
import os
from typing import Dict, Any
from datetime import datetime


def snapshot() -> Dict[str, Any]:
    """
    Create a snapshot export of all JSON files in backend/data.
    
    Returns:
        dict with keys:
            - timestamp (str)
            - files (dict of filename -> content)
            - file_count (int)
    """
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "files": {},
        "file_count": 0
    }
    
    data_dir = "backend/data"
    
    if not os.path.exists(data_dir):
        return result
    
    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        
        # Only process JSON files
        if not filename.endswith(".json") or not os.path.isfile(filepath):
            continue
        
        try:
            with open(filepath, "r") as f:
                content = json.load(f)
                result["files"][filename] = content
                result["file_count"] += 1
        except Exception as e:
            result["files"][filename] = {"error": str(e)}
    
    return result
