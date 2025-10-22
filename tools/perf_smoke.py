import argparse, time, requests

def check(url, p50_target_ms):
    t0 = time.time()
    r = requests.get(url, timeout=10)
    dt = (time.time()-t0)*1000
    assert r.status_code == 200, f"{url} -> {r.status_code}"
    assert dt <= p50_target_ms, f"{url} latency {dt:.1f}ms > {p50_target_ms}ms"
    print(f"OK {url} {dt:.1f}ms")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--p50", type=int, default=300)
    args = ap.parse_args()
    for ep in ["/healthz", "/metrics", "/capital/intake"]:
        check(args.base+ep, args.p50)
