import os

from backend.security.auth import Principal, require_permissions
from backend.utils.signed_url import verify_signed_url
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/download")
async def download_file(
    request: Request,
    path: str = Query(...),
    expiry: int = Query(...),
    token: str = Query(...),
    principal: "Principal" = Depends(require_permissions("files.read")),
):
    import mimetypes

    from backend.db.session import get_session
    from backend.utils.audit import log_event

    client_ip = request.headers.get("x-forwarded-for") or request.client.host
    ua = request.headers.get("user-agent", "")

    if not verify_signed_url(path, expiry, token):
        async with get_session() as s:
            await log_event(
                s,
                org_id=principal.org_id,
                user_id=principal.user_id,
                action="export.download_denied",
                resource=f"file:{path}",
                metadata={"reason": "invalid_signature", "ip": client_ip, "ua": ua},
            )
        raise HTTPException(status_code=403, detail="Invalid or expired link")

    file_path = os.path.join("exports", path)
    if not os.path.exists(file_path):
        async with get_session() as s:
            await log_event(
                s,
                org_id=principal.org_id,
                user_id=principal.user_id,
                action="export.download_denied",
                resource=f"file:{path}",
                metadata={"reason": "not_found", "ip": client_ip, "ua": ua},
            )
        raise HTTPException(status_code=404, detail="File not found")

    async with get_session() as s:
        await log_event(
            s,
            org_id=principal.org_id,
            user_id=principal.user_id,
            action="export.download",
            resource=f"file:{path}",
            metadata={"ip": client_ip, "ua": ua, "bytes": os.path.getsize(file_path)},
        )
    mime, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        file_path,
        media_type=mime or "application/octet-stream",
        filename=os.path.basename(file_path),
    )
