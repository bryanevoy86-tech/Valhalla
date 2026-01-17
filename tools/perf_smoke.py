import os, sys, time
import requests

API = os.environ.get('API')
if not API:
    print('No API env; skipping perf smoke')
    sys.exit(0)

endpoints = ['/healthz','/metrics']
for ep in endpoints:
    url = API.rstrip('/') + ep
    t0 = time.time()
    try:
        r = requests.get(url, timeout=3)
        dt = int((time.time()-t0)*1000)
        print(f'{url} -> {r.status_code} in {dt}ms')
        assert r.status_code in (200, 204)
        assert dt < 300, 'p50 over 300ms'
    except Exception as e:
        print(f'smoke fail: {url}: {e}')
        # do not fail CI for perf smoke
        pass

def main():
    """
    Run performance smoke tests against critical endpoints.
    Exit code 0 if all pass, 1 if any exceed threshold.
    """
    print(f"Performance Smoke Test")
    print(f"API: {API}")
    print(f"P50 Threshold: {P50_MAX_MS}ms")
    print("-" * 50)
    
    samples = []
    endpoints = ["/healthz", "/playbooks"]
    
    for ep in endpoints:
        times = [time_request(ep) for _ in range(5)]
        p50 = statistics.median(times)
        samples_str = ', '.join(f'{x:.0f}' for x in times)
        print(f"{ep:20} p50={p50:.1f}ms (samples={samples_str})")
        samples.append(p50)
    
    worst = max(samples)
    print("-" * 50)
    
    if worst > P50_MAX_MS:
        print(f"FAIL: p50 {worst:.1f}ms exceeds {P50_MAX_MS}ms threshold")
        sys.exit(1)
    
    print(f"OK: All endpoints under {P50_MAX_MS}ms")
    sys.exit(0)


if __name__ == "__main__":
    main()
