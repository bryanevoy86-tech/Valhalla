#!/usr/bin/env python
"""
PACK L, M, N Live Test
Tests Canon, Weekly Audit, and Export Bundle endpoints
"""
import subprocess
import time
import httpx
import sys
import json
from pathlib import Path

BASE_URL = "http://localhost:4000"

def start_server():
    print("Starting uvicorn server...")
    # Kill any existing processes
    subprocess.run(
        'Get-Process python | Where-Object {$_.CommandLine -like "*uvicorn*"} | Stop-Process -Force 2>$null',
        shell=True,
        capture_output=True
    )
    time.sleep(1)
    
    # Start new server
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", "4000",
            "--log-level", "warning"
        ],
        cwd="c:\\dev\\valhalla\\backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)
    return proc

def test_canon():
    print("\n1. Testing GET /core/canon...")
    try:
        resp = httpx.get(f"{BASE_URL}/core/canon", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ Status: {resp.status_code}")
            print(f"  ✓ canon_version: {data.get('canon_version')}")
            print(f"  ✓ locked_model: {data.get('locked_model')}")
            print(f"  ✓ engine_registry: {len(data.get('engine_registry', {}))} engines")
            print(f"  ✓ band_policy: {list(data.get('band_policy', {}).keys())}")
            return True
        else:
            print(f"✗ Status: {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_weekly_audit():
    print("\n2. Testing POST /core/reality/weekly_audit...")
    try:
        resp = httpx.post(f"{BASE_URL}/core/reality/weekly_audit", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ Status: {resp.status_code}")
            if data.get("ok"):
                record = data.get("record", {})
                print(f"  ✓ Audit recorded")
                print(f"  ✓ Timestamp: {record.get('created_at_utc')}")
                print(f"  ✓ Cone band: {record.get('cone', {}).get('band')}")
            return True
        else:
            print(f"✗ Status: {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_weekly_audits_list():
    print("\n3. Testing GET /core/reality/weekly_audits...")
    try:
        resp = httpx.get(f"{BASE_URL}/core/reality/weekly_audits?limit=5", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            print(f"✓ Status: {resp.status_code}")
            print(f"  ✓ Returned {len(items)} audits")
            if items:
                print(f"  ✓ Latest timestamp: {items[0].get('created_at_utc')}")
            return True
        else:
            print(f"✗ Status: {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_export_bundle():
    print("\n4. Testing GET /core/export/bundle...")
    try:
        resp = httpx.get(f"{BASE_URL}/core/export/bundle", timeout=10)
        if resp.status_code == 200:
            print(f"✓ Status: {resp.status_code}")
            print(f"  ✓ Content-Type: {resp.headers.get('content-type')}")
            print(f"  ✓ Content-Length: {len(resp.content)} bytes")
            
            # Try to parse as zip
            import zipfile
            import io
            try:
                z = zipfile.ZipFile(io.BytesIO(resp.content))
                files = z.namelist()
                print(f"  ✓ ZIP contains {len(files)} files:")
                for f in files[:5]:
                    print(f"    - {f}")
                if len(files) > 5:
                    print(f"    ... and {len(files) - 5} more")
                z.close()
                return True
            except Exception as ze:
                print(f"  ✗ Could not parse as ZIP: {ze}")
                return False
        else:
            print(f"✗ Status: {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_go_summary():
    print("\n5. Testing GET /core/go/summary (PACK J)...")
    try:
        resp = httpx.get(f"{BASE_URL}/core/go/summary", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ Status: {resp.status_code}")
            print(f"  ✓ Summary contains data")
            keys = list(data.keys())
            print(f"  ✓ Keys: {keys[:5]}")
            return True
        else:
            print(f"✗ Status: {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("PACK L, M, N Live Test")
    print("=" * 60)
    
    proc = start_server()
    time.sleep(2)
    
    try:
        tests = [
            ("PACK L — Canon", test_canon),
            ("PACK M — Weekly Audit POST", test_weekly_audit),
            ("PACK M — Weekly Audit List", test_weekly_audits_list),
            ("PACK N — Export Bundle", test_export_bundle),
            ("PACK J — Summary (Reference)", test_go_summary),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, result))
            except Exception as e:
                print(f"✗ Test failed: {e}")
                results.append((name, False))
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        passed = sum(1 for _, r in results if r)
        total = len(results)
        
        for name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {name}")
        
        print(f"\n{passed}/{total} tests passed")
        
        if passed == total:
            print("\n✅ All tests passed!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
        
    finally:
        print("\nCleaning up...")
        proc.terminate()
        time.sleep(1)

if __name__ == "__main__":
    main()
