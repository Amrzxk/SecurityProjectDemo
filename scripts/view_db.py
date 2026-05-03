#!/usr/bin/env python3
"""Start sqlite-web UI for instance/app.db (development only).

  pip install -r requirements-dev.txt
  python scripts/view_db.py

Opens http://127.0.0.1:8080 by default with the database read-only to avoid clashes
while the Flask app may be running.

Use --writable only when you intentionally want to edit rows from sqlite-web."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> None:
    default_db = _project_root() / "instance" / "app.db"
    p = argparse.ArgumentParser(description="Open sqlite-web for the project database.")
    p.add_argument(
        "db",
        nargs="?",
        type=Path,
        default=default_db,
        help=f"path to SQLite file (default: {default_db})",
    )
    p.add_argument(
        "--host",
        "-H",
        default="127.0.0.1",
        help="bind host for sqlite-web (default: 127.0.0.1)",
    )
    p.add_argument(
        "--port",
        "-p",
        type=int,
        default=8080,
        help="listen port for sqlite-web (default: 8080)",
    )
    p.add_argument(
        "--writable",
        action="store_true",
        help="omit read-only mode (risky while Flask writes to the same DB)",
    )
    ns = p.parse_args()
    db = ns.db.resolve()
    if not db.is_file():
        print(f"Database not found: {db}", file=sys.stderr)
        sys.exit(1)

    argv = [
        sys.executable,
        "-m",
        "sqlite_web",
        "-H",
        ns.host,
        "-p",
        str(ns.port),
    ]
    if not ns.writable:
        argv.append("--read-only")
    argv.append(str(db))
    raise SystemExit(subprocess.call(argv))


if __name__ == "__main__":
    main()
