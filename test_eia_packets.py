#!/usr/bin/env python
"""Test EIA packet generation and display contents"""

import requests
import json
import zipfile
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Configuration
YEAR = 2026
MONTH = 3
LOCKED_BY = "test_user"

print("=" * 80)
print("EIA PACKET GENERATION TEST")
print("=" * 80)
print(f"Testing packets for {YEAR}-{MONTH:02d}\n")

# Step 1: Open the month
print("\n### STEP 1: OPEN MONTH ###")
open_response = requests.post(
    f"{BASE_URL}/exports/month/open?year={YEAR}&month={MONTH}&opened_by={LOCKED_BY}"
)
print(f"Status: {open_response.status_code}")
print(f"Response: {json.dumps(open_response.json(), indent=2)}")

# Step 2: Generate all packet types
packet_types = ["eia", "accountant", "legal", "appointment"]
packets = {}

for pkg_type in packet_types:
    print(f"\n### GENERATING {pkg_type.upper()} PACKET ###")
    response = requests.post(
        f"{BASE_URL}/exports/packs/{pkg_type if pkg_type != 'appointment' else 'appointment/eia'}?year={YEAR}&month={MONTH}"
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    packets[pkg_type] = data
    print(f"File: {data.get('filename')}")
    print(f"Path: {data.get('file_path')}")
    print(f"Generated: {data.get('generated_at')}")

# Step 3: List available files
print("\n### AVAILABLE FILES ###")
files_response = requests.get(f"{BASE_URL}/exports/packs/files?year={YEAR}&month={MONTH}")
files_data = files_response.json()
print(f"Status: {files_response.status_code}")
print(f"Available Packs: {json.dumps(files_data.get('available_packs'), indent=2)}")

# Step 4: Extract and display ZIP contents
print("\n\n" + "=" * 80)
print("ZIP FILE CONTENTS ANALYSIS")
print("=" * 80)

exports_dir = Path("d:/dev/services/api/app/generated_exports")

for pkg_type in packet_types:
    filename = f"{pkg_type}_pack_{YEAR}_{MONTH:02d}.zip"
    zip_path = exports_dir / filename
    
    if not zip_path.exists():
        print(f"\n❌ {filename} - FILE NOT FOUND at {zip_path}")
        continue
    
    print(f"\n{'=' * 80}")
    print(f"📦 {filename.upper()}")
    print(f"{'=' * 80}")
    print(f"File Size: {zip_path.stat().st_size} bytes")
    print(f"Location: {zip_path}\n")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            print(f"Files in ZIP: {len(zf.namelist())}")
            print("-" * 80)
            
            for file_in_zip in zf.namelist():
                print(f"\n📄 {file_in_zip}")
                content = zf.read(file_in_zip)
                print(f"   Size: {len(content)} bytes")
                
                # Try to parse as JSON
                try:
                    json_content = json.loads(content)
                    print(f"   Content (JSON):")
                    print(json.dumps(json_content, indent=6))
                except:
                    # Display as text
                    text_content = content.decode('utf-8', errors='ignore')
                    if len(text_content) > 500:
                        print(f"   Content (first 500 chars):")
                        print(text_content[:500])
                    else:
                        print(f"   Content:")
                        print(text_content)
    except Exception as e:
        print(f"❌ Error reading ZIP: {e}")

# Step 5: Close the month
print("\n\n" + "=" * 80)
print("CLOSING MONTH")
print("=" * 80)
close_response = requests.post(
    f"{BASE_URL}/exports/packs/appointment/eia/close?year={YEAR}&month={MONTH}&locked_by={LOCKED_BY}"
)
print(f"Status: {close_response.status_code}")
print(f"Response: {json.dumps(close_response.json(), indent=2)}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
