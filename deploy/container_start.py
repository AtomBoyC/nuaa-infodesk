"""Validate deployment configuration and migrate the persistent database."""

from __future__ import annotations

import os
import sys

from database import DEFAULT_DB_PATH, bootstrap_database
from maintenance_auth import admin_password


def main() -> None:
    if admin_password() is None:
        raise RuntimeError("A password file is required for the container deployment.")
    connection = bootstrap_database(DEFAULT_DB_PATH)
    try:
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError("Knowledge database integrity check failed.")
    finally:
        connection.close()
    if len(sys.argv) < 2:
        raise RuntimeError("No container command was supplied.")
    os.execvp(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    main()
