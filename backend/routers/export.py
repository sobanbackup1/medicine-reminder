"""CSV export of medication history (admin only)."""

from __future__ import annotations

import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import crud
from ..auth import require_admin
from ..database import get_db_dep

router = APIRouter(prefix="/api/export", tags=["export"], dependencies=[Depends(require_admin)])


@router.get("/csv")
def export_csv(db: Session = Depends(get_db_dep)):
    logs = crud.list_all_logs(db)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "status", "action_timestamp", "created_at", "updated_at"])
    for l in logs:
        writer.writerow([
            l.log_date.isoformat(),
            l.status,
            l.action_timestamp.isoformat() if l.action_timestamp else "",
            l.created_at.isoformat() if l.created_at else "",
            l.updated_at.isoformat() if l.updated_at else "",
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=medication_history.csv"},
    )
