def run_backend_tests():
    import requests
    endpoints = [
        "/api/health", "/api/launch/status", "/api/eia/status", "/api/eia/monthly-report"
    ]
    for endpoint in endpoints:
        response = requests.get(f"http://localhost:8000{endpoint}")
        if response.status_code != 200:
            print(f"ERROR: {endpoint} failed")
            return False
    return True

if __name__ == "__main__":
    if run_backend_tests():
        print("All tests passed!")
    else:
        print("Some tests failed!")
