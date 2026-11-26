import hmac
import time
from hashlib import sha256

from pydantic import BaseModel
from fastapi import APIRouter, status, Request, Response, Depends

from src.core.auth import verify_api_key
from src.core.settings import settings

# so it can't itself sit behind the same pre-shared-key dependency as the
# rest of the v1 router.
router = APIRouter(prefix="/v1")

class GetHealth(BaseModel):
    message: str
    status_code: int
@router.get(
    "/health",
    response_model=GetHealth,
)
async def get_health():
    """Health check endpoint"""
    return GetHealth(
        message="healthy",
        status_code=status.HTTP_200_OK
    )


@router.get("/session")
async def get_session(response: Response):
    """Mint a short-lived anonymous session token for WS auth."""
    expiry = str(int(time.time()) + settings.session_token_ttl)
    sig = hmac.new(
        settings.session_secret_key.encode(), expiry.encode(), sha256
    ).hexdigest()
    response.set_cookie(
        key="session_token",
        value=f"{expiry}.{sig}",
        max_age=settings.session_token_ttl,
        httponly=True,
        secure=True,
        samesite="none",
    )
    return {"status_code": status.HTTP_200_OK}


@router.get("/agent/graph", dependencies=[Depends(verify_api_key)])
async def get_agent_graph(request: Request):
    """Return the compiled agent graph as a PNG image."""
    return Response(
        content=request.app.state.nyeh_agent_graph_png,
        media_type="image/png",
    )