"""Backup endpoints (admin only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import crud, backup
from ..auth import require_admin
from ..database import get_db_dep
from ..schemas import BackupOut

router = APIRouter(prefix="/api/backup", tags=["backup"], dependencies=[Depends(require_admin)])


@router.get("", response_model=list[BackupOut])
def list_backups(db: Session = Depends(get_db_dep)):
    rows = crud.list_backups(db)
    return [BackupOut(
        id=r.id, created_at=r.created_at, filename=r.filename,
        file_size=r.file_size, success=r.success, error_message=r.error_message,
    ) for r in rows]


@router.post("")
def create_backup():
    success, filename, size = backup.create_backup()
    return {"success": success, "filename": filename, "size": size}


@router.get("/download/{filename}")
def download_backup(filename: str):
    from pathlib import Path
    from ..config import env
    backup_root = Path(env.backup_dir).resolve()
    filepath = (backup_root / filename).resolve()
    if not filepath.is_relative_to(backup_root) or not filepath.is_file():
        from fastapi import HTTPException
        raise HTTPException(404, "Backup not found")
    return FileResponse(filepath, filename=filename, media_type="application/sql")
