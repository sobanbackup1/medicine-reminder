"""Database backup utilities.

Creates timestamped SQL dumps using the mysqldump CLI.  Falls back to a
Python-only row export if mysqldump is unavailable so the feature still works.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from sqlalchemy import MetaData, select

from .config import env
from .database import engine, get_db
from . import crud, models

logger = logging.getLogger(__name__)


def ensure_backup_dir() -> Path:
    p = Path(env.backup_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def create_backup() -> tuple[bool, str, int | None]:
    """Create a backup.  Returns (success, filename, size_bytes)."""
    backup_dir = ensure_backup_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"medication_backup_{stamp}.sql"
    filepath = backup_dir / filename

    # Try mysqldump first
    if shutil.which("mysqldump"):
        try:
            cmd = [
                "mysqldump",
                f"--host={env.mysql_host}",
                f"--port={env.mysql_port}",
                f"--user={env.mysql_user}",
                env.mysql_database,
            ]
            dump_env = os.environ.copy()
            dump_env["MYSQL_PWD"] = env.mysql_password
            with open(filepath, "wb") as f:
                subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True, env=dump_env)
            size = filepath.stat().st_size
            _log_backup(filename, size, True, None)
            return True, filename, size
        except subprocess.CalledProcessError as exc:
            err = exc.stderr.decode("utf-8", "replace") if exc.stderr else str(exc)
            _log_backup(filename, None, False, err)
            logger.error("mysqldump failed: %s", err)
            # fall through to python fallback

    # Python fallback: dump all tables as INSERT statements
    try:
        _python_dump(filepath)
        size = filepath.stat().st_size
        _log_backup(filename, size, True, None)
        return True, filename, size
    except Exception as exc:
        _log_backup(filename, None, False, str(exc))
        return False, filename, None


def _python_dump(filepath: Path) -> None:
    """Minimal SQL dump via SQLAlchemy (no external tools)."""
    md = MetaData()
    md.reflect(bind=engine)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"-- Medication backup {datetime.now().isoformat()}\n")
        f.write("SET FOREIGN_KEY_CHECKS=0;\n")
        with get_db() as db:
            for table in md.sorted_tables:
                f.write(f"\n-- Table {table.name}\n")
                f.write(f"TRUNCATE TABLE `{table.name}`;\n")
                rows = db.execute(select(table)).fetchall()
                for row in rows:
                    cols = table.columns.keys()
                    values = []
                    for col in cols:
                        v = getattr(row, col)
                        if v is None:
                            values.append("NULL")
                        elif isinstance(v, (int, float)):
                            values.append(str(v))
                        elif isinstance(v, datetime):
                            values.append(f"'{v.isoformat()}'")
                        else:
                            escaped = str(v).replace("'", "''")
                            values.append(f"'{escaped}'")
                    col_list = ", ".join(f"`{c}`" for c in cols)
                    val_list = ", ".join(values)
                    f.write(
                        f"INSERT INTO `{table.name}` ({col_list}) VALUES ({val_list});\n"
                    )
        f.write("SET FOREIGN_KEY_CHECKS=1;\n")


def _log_backup(filename: str, size: int | None, success: bool, error: str | None) -> None:
    with get_db() as db:
        crud.add_backup_log(db, filename, size, success, error)


def list_backup_files() -> list[Path]:
    d = ensure_backup_dir()
    return sorted(d.glob("*.sql"), reverse=True)
