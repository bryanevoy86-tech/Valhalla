from fastapi import APIRouter

from app.core.build_info import get_runtime_build_identity

router = APIRouter(tags=["deployment"])

@router.get("/deployment-marker")
def get_deployment_marker():
    identity = get_runtime_build_identity()
    return {
        "status": "ok",
        "timestamp": identity["observed_at"],
        "message": f"Deployment identity from {identity['git_sha_source']}",
        "commit": identity["git_sha"],
        "commit_short": identity["git_sha_short"],
        "commit_source": identity["git_sha_source"],
        "version": identity["version"],
        "built_at": identity["built_at"],
        "buildinfo_path": identity["buildinfo_path"],
        "endpoint": "GET /deployment-marker",
    }
