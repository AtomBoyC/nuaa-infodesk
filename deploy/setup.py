"""Create local deployment configuration without replacing existing secrets."""

from __future__ import annotations

import os
from pathlib import Path
import secrets
import shutil


def initialize_deployment(project: Path) -> list[Path]:
    created = []
    env_file = project / ".env"
    if not env_file.exists():
        shutil.copyfile(project / ".env.example", env_file)
        created.append(env_file)

    secret_directory = project / ".secrets"
    secret_directory.mkdir(mode=0o700, exist_ok=True)
    password_file = secret_directory / "admin_password"
    try:
        descriptor = os.open(password_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError:
        if len(password_file.read_text(encoding="utf-8").rstrip("\r\n")) < 16:
            raise ValueError("Existing administrator password must contain at least 16 characters.")
    else:
        # The private host directory protects the file; its bind mount must also
        # be readable by the non-root UID running inside the application image.
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(secrets.token_urlsafe(32) + "\n")
        password_file.chmod(0o444)
        created.append(password_file)
    return created


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    for path in initialize_deployment(project):
        print(f"Created {path.relative_to(project)}")
    print("Deployment configuration is ready. Existing files were preserved.")
    print("Administrator password: .secrets/admin_password (not printed).")


if __name__ == "__main__":
    main()
