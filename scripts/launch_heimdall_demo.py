#!/usr/bin/env python3
"""Start Heimdall on this computer with a new PostgreSQL cluster each time."""

import argparse
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
DB = "heimdall_demo"
OWNER = "owner@heimdall-demo.invalid"


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def postgres_tools(directory):
    suffix = ".exe" if os.name == "nt" else ""
    if directory is None:
        initdb = shutil.which("initdb")
        directory = Path(initdb).parent if initdb else None
    if directory is None and os.name == "nt":
        installations = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "PostgreSQL"
        candidates = sorted(installations.glob("*/bin/initdb.exe"), reverse=True)
        directory = candidates[0].parent if candidates else None
    if directory is None:
        raise ValueError("PostgreSQL was not found. Install the local PostgreSQL tools or pass --pg-bin.")
    tools = tuple(directory.resolve() / (name + suffix) for name in ("initdb", "pg_ctl"))
    if not all(path.is_file() for path in tools):
        raise ValueError("--pg-bin must point to the PostgreSQL folder containing initdb and pg_ctl.")
    return tools


def demo_environment(workdir):
    platform = ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR", "USERPROFILE",
                "APPDATA", "LOCALAPPDATA", "HOME", "COMSPEC", "SystemDrive")
    env = {key: os.environ[key] for key in platform if key in os.environ}
    env.update(PYTHONPATH=str(ROOT / "services" / "api"), PYTHON_DOTENV_DISABLED="1",
               APP_ENV="dev", ENV="dev", VALHALLA_EMERGENCY_STOP="true",
               VALHALLA_AUTH_ENABLED="true", VALHALLA_OWNER_EMAIL=OWNER,
               VALHALLA_OWNER_USERNAME="demo-owner", VALHALLA_OWNER_PASSWORD=secrets.token_urlsafe(18),
               VALHALLA_JWT_SECRET=secrets.token_urlsafe(48), HEIMDALL_DEMO_DIR=str(workdir),
               PYTHONUNBUFFERED="1")
    return env


def run_demo(initdb, pg_ctl, port):
    with TemporaryDirectory(prefix="heimdall-demo-") as temporary:
        workdir = Path(temporary)
        env = demo_environment(workdir)
        data = workdir / "postgres"
        db_port = free_port()
        if db_port == port:
            db_port = free_port()
        db_password = secrets.token_hex(24)
        password_file = workdir / "init-password"
        password_file.write_text(db_password + "\n", encoding="ascii")
        try:
            subprocess.run([initdb, "-D", data, "--username", DB, "--pwfile", password_file,
                            "--auth=scram-sha-256", "--encoding=UTF8", "--no-locale"],
                           cwd=workdir, env=env, check=True, stdout=subprocess.DEVNULL, timeout=90)
        finally:
            password_file.unlink(missing_ok=True)

        with (data / "postgresql.conf").open("a", encoding="utf-8") as config:
            config.write(f"\nlisten_addresses = '127.0.0.1'\nport = {db_port}\nunix_socket_directories = ''\n")
        try:
            subprocess.run([pg_ctl, "-D", data, "-l", workdir / "postgres.log", "-w", "start"],
                           cwd=workdir, env=env, check=True, timeout=90)
            env.update(DATABASE_URL=f"postgresql+psycopg2://{DB}:{db_password}@127.0.0.1:{db_port}/postgres",
                       HEIMDALL_DEMO_PORT=str(port))
            with subprocess.Popen([sys.executable, ROOT / "scripts" / "heimdall_demo" / "server.py"],
                                  cwd=workdir, env=env) as server:
                try:
                    return server.wait()
                except KeyboardInterrupt:
                    if server.poll() is None:
                        server.terminate()
                        server.wait(timeout=15)
                    return 0
        finally:
            if (data / "postmaster.pid").exists():
                subprocess.run([pg_ctl, "-D", data, "-m", "fast", "-w", "stop"],
                               cwd=workdir, env=env, check=True, timeout=90)
            print("Heimdall demo stopped. The disposable database is being removed.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-bin", type=Path, help="Local PostgreSQL bin folder")
    parser.add_argument("--port", type=int, default=8765, help="Local browser port, default 8765")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Use a browser port between 1024 and 65535.")
    try:
        return run_demo(*postgres_tools(args.pg_bin), args.port)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"Heimdall demo could not finish: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
