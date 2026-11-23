#!/usr/bin/env python3
"""Rehearse the owner's launch command, browser flow and disposable shutdown."""

import argparse
import json
import os
from pathlib import Path
from queue import Empty, Queue
import signal
import subprocess
import sys
from threading import Thread
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-bin", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen([sys.executable, ROOT / "scripts/launch_heimdall_demo.py",
                                "--pg-bin", args.pg_bin.resolve(), "--port", "18765"],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                               creationflags=flags)
    lines = Queue()
    logs = []

    def read_output():
        for line in process.stdout:
            if line.startswith("One-run demo password:"):
                lines.put(line.split(":", 1)[1].strip())
            else:
                logs.append(line)

    reader = Thread(target=read_output, daemon=True)
    reader.start()
    origin = "http://127.0.0.1:18765"
    client = build_opener(ProxyHandler({}))

    def check(path, expected, method="GET", headers=None):
        request = Request(origin + path, method=method, headers=headers or {})
        try:
            response = client.open(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            assert response.code == expected, (path, response.code, expected)

    try:
        deadline = monotonic() + 100
        while True:
            try:
                password = lines.get(timeout=0.3)
                break
            except Empty:
                if process.poll() is not None or monotonic() >= deadline:
                    raise RuntimeError("Local demo did not start\n" + "".join(logs[-20:])) from None
        check("/demo/", 200)
        check("/api/weweb/owner-pantheon/reports", 401)
        check("/api/weweb/owner-pantheon/reports", 403, headers={"Origin": "http://localhost:18765"})
        check("/api/weweb/reset-owner-password", 404, "POST")
        check("/webhooks/stripe", 404, "POST")
        check("/governance/execute", 404, "POST")
        check("/demo/", 400, headers={"Host": "demo.invalid"})
        result = subprocess.run(["node", ROOT / "tests/browser-acceptance/owner-demo.cjs"],
                                input=json.dumps({"origin": origin, "password": password}), text=True,
                                capture_output=True, check=False, timeout=100)
        if result.returncode:
            raise RuntimeError(result.stderr)
        report = json.loads(result.stdout)
    finally:
        if process.poll() is None:
            process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)
        process.wait(timeout=40)
        reader.join(timeout=5)
    assert process.returncode == 0 and any("disposable database is being removed" in line for line in logs)
    try:
        client.open(origin + "/demo/", timeout=2)
    except URLError as error:
        assert isinstance(error.reason, ConnectionRefusedError), error
    else:
        raise AssertionError("Demo still responds after stop")
    report.update(shutdown="PASSED", anonymous="401", foreign_origin="403", commercial_routes="404",
                  revision=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip())
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
