"""Password-file authentication for the knowledge maintenance page."""

from __future__ import annotations

import hmac
import os
from pathlib import Path


def admin_password() -> str | None:
    password_file = os.environ.get("INFODESK_ADMIN_PASSWORD_FILE", "")
    required = os.environ.get("INFODESK_REQUIRE_ADMIN_PASSWORD", "").lower() in {
        "1", "true", "yes",
    }
    if not password_file:
        if required:
            raise RuntimeError("Administrator password file is not configured.")
        return None
    try:
        password = Path(password_file).read_text(encoding="utf-8").rstrip("\r\n")
    except OSError as error:
        raise RuntimeError("Administrator password file cannot be read.") from error
    if len(password) < 16:
        raise RuntimeError("Administrator password must contain at least 16 characters.")
    return password


def password_matches(candidate: str, expected: str) -> bool:
    return hmac.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))
