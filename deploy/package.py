"""Package deployment files and a consistent SQLite snapshot for SSH upload."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import tarfile
import tempfile


DEPLOYMENT_FILES = (
    "Dockerfile", ".dockerignore", ".gitignore", ".env.example", "compose.yaml", "compose.https.yaml",
    "requirements.txt", "README.md", "streamlit_app.py", "database.py",
    "info_service_assistant.py", "maintenance_auth.py", "knowledge_taxonomy.py",
    "knowledge_dedup.py", "site_importer.py", "docx_importer.py", "check_knowledge.py",
    "deploy/setup.py", "deploy/package.py", "deploy/container_start.py",
    "deploy/database_backup.py", "deploy/Caddyfile", "docs/docker-compose.md",
    "docs/project-audit.md", "docs/submission-checklist.md",
)


def package_project(project: Path, output: Path) -> None:
    for name in (*DEPLOYMENT_FILES, "data/info_service.db"):
        if not (project / name).is_file():
            raise FileNotFoundError(f"Required deployment file is missing: {name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        snapshot = Path(directory) / "info_service.db"
        source_path = (project / "data" / "info_service.db").resolve()
        source = sqlite3.connect(f"{source_path.as_uri()}?mode=ro", uri=True)
        target = sqlite3.connect(snapshot)
        try:
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Knowledge database integrity check failed.")
        finally:
            target.close()
            source.close()

        with tarfile.open(output, "x:gz") as archive:
            for name in DEPLOYMENT_FILES:
                archive.add(project / name, arcname=name)
            archive.add(snapshot, arcname="data/info_service.db")


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or project / "outputs" / f"nuaa-infodesk-deploy-{timestamp}.tar.gz"
    package_project(project, output)
    print(f"Deployment package saved: {output}")


if __name__ == "__main__":
    main()
