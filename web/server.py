import json
import time as _time
import asyncio
import logging
from os import getenv
from urllib.parse import urlencode

import httpx
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature

log = logging.getLogger(__name__)

DISCORD_CLIENT_ID = getenv("DISCORD__CLIENT_ID", "")
DISCORD_CLIENT_SECRET = getenv("DISCORD__CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = getenv("DISCORD__REDIRECT_URI", "")
SECRET_KEY = getenv("WEB_SECRET_KEY", "wavox-change-me-in-prod")
REDIS_URL = getenv("REDIS_URL", "redis://redis:6379/0")
SESSION_MAX_AGE = 86400  # 24h

signer = URLSafeTimedSerializer(SECRET_KEY)
_redis: redis.Redis | None = None

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.on_event("startup")
async def startup():
    global _redis
    _redis = redis.from_url(REDIS_URL, decode_responses=True)


@app.on_event("shutdown")
async def shutdown():
    if _redis:
        await _redis.aclose()


# --- Session helpers ---

def _get_session(request: Request) -> dict | None:
    token = request.cookies.get("wavox_session")
    if not token:
        return None
    try:
        return signer.loads(token, max_age=SESSION_MAX_AGE)
    except BadSignature:
        return None


def _set_session(response, data: dict):
    token = signer.dumps(data)
    response.set_cookie(
        "wavox_session", token,
        httponly=True, secure=True, samesite="lax",
        max_age=SESSION_MAX_AGE,
    )


# --- Discord OAuth2 ---

DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API = "https://discord.com/api/v10"


@app.get("/dashboard/login")
async def login():
    params = urlencode({
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
    })
    return RedirectResponse(f"{DISCORD_AUTH_URL}?{params}")


@app.get("/dashboard/callback")
async def callback(code: str):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(DISCORD_TOKEN_URL, data={
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
        })
        if token_resp.status_code != 200:
            raise HTTPException(400, "OAuth2 token exchange failed")
        tokens = token_resp.json()

        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        user_resp = await client.get(f"{DISCORD_API}/users/@me", headers=headers)
        if user_resp.status_code != 200:
            raise HTTPException(400, "Failed to get user info")
        user = user_resp.json()

        guilds_resp = await client.get(f"{DISCORD_API}/users/@me/guilds", headers=headers)
        guilds = guilds_resp.json() if guilds_resp.status_code == 200 else []

    session_data = {
        "user_id": user["id"],
        "username": user["username"],
        "avatar": user.get("avatar"),
        "guilds": [{"id": g["id"], "name": g["name"], "icon": g.get("icon")} for g in guilds],
    }

    response = RedirectResponse("/dashboard")
    _set_session(response, session_data)
    return response


@app.get("/dashboard/logout")
async def logout():
    response = RedirectResponse("/dashboard")
    response.delete_cookie("wavox_session")
    return response


def _guild_ids(session: dict) -> list[str]:
    return [g["id"] for g in session.get("guilds", [])]


# --- API ---

@app.get("/api/me")
async def api_me(request: Request):
    session = _get_session(request)
    if not session:
        raise HTTPException(401)

    active = await _redis.smembers("wavox:active_guilds")
    guilds = [g for g in session.get("guilds", []) if g["id"] in active]

    return JSONResponse({
        "user_id": session["user_id"],
        "username": session["username"],
        "avatar": session.get("avatar"),
        "guilds": guilds,
    })


@app.get("/api/guilds/{guild_id}/status")
async def api_guild_status(guild_id: str, request: Request):
    session = _get_session(request)
    if not session:
        raise HTTPException(401)
    if guild_id not in _guild_ids(session):
        raise HTTPException(403, "Not a member of this guild")

    raw = await _redis.get(f"wavox:guild:{guild_id}:state")
    if not raw:
        return JSONResponse({"now_playing": None, "queue": [], "is_playing": False, "is_paused": False, "loop_mode": "off"})
    data = json.loads(raw)
    return JSONResponse(data.get("data", data))


@app.post("/api/guilds/{guild_id}/playback")
async def api_playback(guild_id: str, request: Request):
    session = _get_session(request)
    if not session:
        raise HTTPException(401)
    if guild_id not in _guild_ids(session):
        raise HTTPException(403, "Not a member of this guild")

    body = await request.json()
    action = body.get("action")
    if action not in ("pause", "resume", "skip", "previous", "shuffle", "loop", "goto", "stop", "clear", "play", "skip_to"):
        raise HTTPException(400, "Invalid action")

    cmd = {"guild_id": guild_id, "action": action, "user_id": session["user_id"]}
    if action == "goto":
        cmd["position"] = body.get("position", "0")
    elif action == "skip_to":
        cmd["position"] = body.get("position", 1)
    elif action == "play":
        cmd["query"] = body.get("query", "")

    await _redis.publish("wavox:commands", json.dumps(cmd))
    return JSONResponse({"ok": True})


@app.get("/api/search")
async def api_search(q: str, request: Request):
    session = _get_session(request)
    if not session:
        raise HTTPException(401)

    guild_id = request.query_params.get("guild_id", "")
    if not guild_id or guild_id not in _guild_ids(session):
        raise HTTPException(400, "guild_id required")

    request_id = f"search_{session['user_id']}_{int(_time.time() * 1000)}"
    await _redis.publish("wavox:commands", json.dumps({
        "guild_id": guild_id,
        "action": "search",
        "query": q,
        "request_id": request_id,
    }))

    result = await _redis.blpop(f"wavox:response:{request_id}", timeout=10)
    if not result:
        return JSONResponse([])
    return JSONResponse(json.loads(result[1]))


@app.get("/api/lyrics")
async def api_lyrics(q: str, request: Request):
    session = _get_session(request)
    if not session:
        raise HTTPException(401)

    for suffix in ['(Official Audio)', '(Official Video)', '(Lyrics)',
                   '(Official Music Video)', '[Official Audio]', '[Official Video]',
                   '(Audio)', '(Video)', '- Topic']:
        q = q.replace(suffix, '')
    q = q.strip()

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://lrclib.net/api/search",
            params={"q": q},
            timeout=10.0,
        )
        if resp.status_code != 200:
            return JSONResponse({"synced": None, "plain": None})
        results = resp.json()
        if not results:
            return JSONResponse({"synced": None, "plain": None})
        best = results[0]
        return JSONResponse({
            "synced": best.get("syncedLyrics"),
            "plain": best.get("plainLyrics"),
            "artist": best.get("artistName", ""),
            "title": best.get("trackName", ""),
        })


@app.get("/api/guilds/{guild_id}/user-status")
async def api_user_status(guild_id: str, request: Request):
    session = _get_session(request)
    if not session:
        raise HTTPException(401)
    if guild_id not in _guild_ids(session):
        raise HTTPException(403)

    request_id = f"status_{session['user_id']}_{guild_id}_{int(_time.time() * 1000)}"
    await _redis.publish("wavox:commands", json.dumps({
        "guild_id": guild_id,
        "action": "get_user_status",
        "user_id": session["user_id"],
        "request_id": request_id,
    }))

    result = await _redis.blpop(f"wavox:response:{request_id}", timeout=5)
    if not result:
        return JSONResponse({})
    return JSONResponse(json.loads(result[1]))


# --- WebSocket (Redis pub/sub per connection) ---

@app.websocket("/api/guilds/{guild_id}/ws")
async def ws_guild(websocket: WebSocket, guild_id: str):
    session = _get_session(websocket)
    if not session or guild_id not in _guild_ids(session):
        await websocket.close(code=4003)
        return

    await websocket.accept()

    pubsub = _redis.pubsub()
    await pubsub.subscribe(f"wavox:events:{guild_id}")

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                await websocket.send_text(message["data"])
            except WebSocketDisconnect:
                return
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        await pubsub.unsubscribe(f"wavox:events:{guild_id}")
        await pubsub.aclose()


# --- Dashboard page ---

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    with open("/web/templates/dashboard.html") as f:
        return HTMLResponse(f.read())


# --- Static site (mkdocs) - must be last ---
app.mount("/", StaticFiles(directory="/web/site", html=True), name="site")
