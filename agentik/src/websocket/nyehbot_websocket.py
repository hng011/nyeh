import asyncio
import hmac
import logging
import time
from collections import deque
from hashlib import sha256

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from src.core.settings import settings
from src.service.nyehbot_service import generate_answer

logger = logging.getLogger(__name__)

ws_router = APIRouter(prefix="/v1")

_active_connections: dict[str, int] = {}
# shortcut: in-memory, one entry per IP never evicted, single replica only; move to Redis if scaling out.
_ip_message_times: dict[str, deque] = {}


def _client_ip(ws: WebSocket) -> str:
    # Only reachable through Traefik, which sets X-Forwarded-For; first hop is the visitor.
    forwarded = ws.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (ws.client.host if ws.client else "unknown")


def _ip_allowed(ip: str, now: float) -> bool:
    times = _ip_message_times.setdefault(ip, deque())
    while times and now - times[0] > settings.ip_rate_window:
        times.popleft()
    if len(times) >= settings.ip_rate_limit:
        return False
    times.append(now)
    return True


def _verify_session_token(token: str) -> bool:
    try:
        expiry_ts, sig = token.split(".", 1)
    except ValueError:
        return False
    expected_sig = hmac.new(
        settings.session_secret_key.encode(), expiry_ts.encode(), sha256
    ).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return False
    try:
        return int(expiry_ts) > time.time()
    except ValueError:
        return False


@ws_router.websocket("/chat/{session_id}")
async def chat_websocket(
    ws: WebSocket,
    session_id: str
):
    token = ws.cookies.get("session_token", "")
    if not _verify_session_token(token):
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    origin = ws.headers.get("origin")
    allowed_origins = settings.cors_origins
    if allowed_origins != ["*"] and origin not in allowed_origins:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    conn_key = sha256(token.encode()).hexdigest()
    if _active_connections.get(conn_key, 0) >= settings.ws_max_connections_per_key:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws.accept()
    _active_connections[conn_key] = _active_connections.get(conn_key, 0) + 1
    message_times: deque = deque()

    try:
        while True:
            try:
                user_message = await asyncio.wait_for(
                    ws.receive_text(), timeout=settings.ws_idle_timeout
                )
            except asyncio.TimeoutError:
                await ws.close(code=status.WS_1000_NORMAL_CLOSURE)
                break

            if len(user_message) > settings.ws_max_msg_size:
                await ws.close(code=status.WS_1009_MESSAGE_TOO_BIG)
                break

            now = time.monotonic()
            while message_times and now - message_times[0] > settings.ws_rate_window:
                message_times.popleft()
            message_times.append(now)
            if len(message_times) > settings.ws_rate_limit:
                await ws.close(code=status.WS_1008_POLICY_VIOLATION)
                break

            if not _ip_allowed(_client_ip(ws), now):
                await ws.send_text("error: too many messages, please try again later")
                continue

            try:
                answer = await generate_answer(
                    user_message=user_message,
                    thread_id=session_id,
                    agent=ws.app.state.nyeh_agent
                )
            except ValueError as exc:
                await ws.send_text(f"error: {exc}")
                continue
            except Exception:
                logger.exception("thread=%s failed to generate answer", session_id)
                await ws.send_text("error: something went wrong, please try again")
                continue
            await ws.send_text(answer)

    except WebSocketDisconnect:
        pass
    finally:
        _active_connections[conn_key] -= 1
        if _active_connections[conn_key] <= 0:
            del _active_connections[conn_key]
