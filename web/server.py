import json
import time as _time
import asyncio
import logging
import secrets
from os import getenv
from urllib.parse import urlencode

import httpx
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature, BadTimeSignature

log = logging.getLogger(__name__)

DISCORD_CLIENT_ID = getenv("DISCORD__CLIENT_ID", "")
DISCORD_CLIENT_SECRET = getenv("DISCORD__CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = getenv("DISCORD__REDIRECT_URI", "")
SECRET_KEY = getenv("WEB_SECRET_KEY", "wavox-change-me-in-prod")
REDIS_URL = getenv("REDIS_URL", "redis://redis:6379/0")
SESSION_MAX_AGE = 86400  # 24h
OAUTH_STATE_MAX_AGE = 600  # 10m
WEB_ORIGIN = getenv("WEB_ORIGIN", "")
COOKIE_SECURE = getenv("WEB_COOKIE_SECURE", "true" if WEB_ORIGIN.startswith("https://") else "false").lower() in {
    "1", "true", "yes", "on"
}

# Discord permission bitflags
PERM_ADMINISTRATOR = 0x8
PERM_MANAGE_GUILD = 0x20

signer = URLSafeTimedSerializer(SECRET_KEY)
state_signer = URLSafeTimedSerializer(f"{SECRET_KEY}:oauth-state")
_redis: redis.Redis | None = None
_lyrics_cache: dict[str, tuple[float, dict]] = {}
LYRICS_CACHE_TTL = 3600

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
        httponly=True, secure=COOKIE_SECURE, samesite="lax",
        max_age=SESSION_MAX_AGE,
    )


def _set_oauth_state(response, state: str):
    response.set_cookie(
        "wavox_oauth_state",
        state_signer.dumps(state),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=OAUTH_STATE_MAX_AGE,
    )


def _pop_oauth_state(response):
    response.delete_cookie("wavox_oauth_state")


def _verify_oauth_state(request: Request, state: str):
    token = request.cookies.get("wavox_oauth_state")
    if not token or not state:
        raise HTTPException(400, "OAuth2 state is missing")
    try:
        expected = state_signer.loads(token, max_age=OAUTH_STATE_MAX_AGE)
    except (BadSignature, BadTimeSignature):
        raise HTTPException(400, "OAuth2 state is invalid")
    if not secrets.compare_digest(str(expected), state):
        raise HTTPException(400, "OAuth2 state is invalid")


def _is_guild_admin(guild: dict) -> bool:
    """Admin = guild owner OR has ADMINISTRATOR / MANAGE_GUILD permission."""
    if guild.get("owner"):
        return True
    try:
        perms = int(guild.get("permissions", 0))
    except (TypeError, ValueError):
        return False
    return bool(perms & (PERM_ADMINISTRATOR | PERM_MANAGE_GUILD))


# --- Discord OAuth2 ---

DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API = "https://discord.com/api/v10"


@app.get("/dashboard/login")
async def login():
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET or not DISCORD_REDIRECT_URI:
        raise HTTPException(500, "Discord OAuth2 is not configured")

    state = secrets.token_urlsafe(32)
    params = urlencode({
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
        "state": state,
    })
    response = RedirectResponse(f"{DISCORD_AUTH_URL}?{params}")
    _set_oauth_state(response, state)
    return response


@app.get("/dashboard/callback")
async def callback(code: str, state: str, request: Request):
    _verify_oauth_state(request, state)

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
        "guilds": [
            {
                "id": g["id"],
                "name": g["name"],
                "icon": g.get("icon"),
                "is_admin": _is_guild_admin(g),
            }
            for g in guilds
        ],
    }

    response = RedirectResponse("/app")
    _pop_oauth_state(response)
    _set_session(response, session_data)
    return response


@app.get("/dashboard/logout")
async def logout():
    response = RedirectResponse("/")
    response.delete_cookie("wavox_session")
    response.delete_cookie("wavox_oauth_state")
    return response


def _guild_ids(session: dict) -> list[str]:
    return [g["id"] for g in session.get("guilds", [])]


def _admin_guild_ids(session: dict) -> list[str]:
    return [g["id"] for g in session.get("guilds", []) if g.get("is_admin")]


def _require_session(request: Request) -> dict:
    session = _get_session(request)
    if not session:
        raise HTTPException(401)
    return session


def _require_admin(session: dict, guild_id: str):
    if guild_id not in _admin_guild_ids(session):
        raise HTTPException(403, "Admin access required for this guild")


async def _require_guild_access(session: dict, guild_id: str):
    if guild_id not in _guild_ids(session):
        raise HTTPException(403, "Not a member of this guild")
    if not _redis:
        raise HTTPException(503, "Backend is not ready")
    if not await _redis.sismember("wavox:active_guilds", guild_id):
        raise HTTPException(403, "Bot is not active in this guild")


async def _require_admin_guild_access(session: dict, guild_id: str):
    _require_admin(session, guild_id)
    if not _redis:
        raise HTTPException(503, "Backend is not ready")
    if not await _redis.sismember("wavox:active_guilds", guild_id):
        raise HTTPException(403, "Bot is not active in this guild")


def _empty_guild_state() -> dict:
    return {
        "now_playing": None,
        "queue": [],
        "is_playing": False,
        "is_paused": False,
        "loop_mode": "off",
    }


def _normalize_guild_state(raw_state: dict | None) -> dict:
    if not isinstance(raw_state, dict):
        return _empty_guild_state()

    state = raw_state.get("data", raw_state)
    if not isinstance(state, dict):
        return _empty_guild_state()

    normalized = _empty_guild_state()
    now_playing = state.get("now_playing")
    if isinstance(now_playing, dict):
        normalized["now_playing"] = {
            "title": now_playing.get("title"),
            "thumbnail": now_playing.get("thumbnail"),
            "webpage_url": now_playing.get("webpage_url"),
            "duration": now_playing.get("duration"),
            "started_at": now_playing.get("started_at") or 0,
            "offset": now_playing.get("offset") or 0,
            "paused_at": now_playing.get("paused_at"),
            "elapsed": now_playing.get("elapsed") or 0,
        }

    queue = state.get("queue")
    if isinstance(queue, list):
        normalized["queue"] = [
            {
                "title": item.get("title") if isinstance(item, dict) else None,
                "duration": item.get("duration") if isinstance(item, dict) else None,
            }
            for item in queue
            if isinstance(item, dict)
        ]

    normalized["is_playing"] = bool(state.get("is_playing"))
    normalized["is_paused"] = bool(state.get("is_paused"))
    if state.get("loop_mode") in {"off", "track", "queue"}:
        normalized["loop_mode"] = state["loop_mode"]

    return normalized


async def _get_cached_guild_state(guild_id: str) -> dict:
    if not _redis:
        return _empty_guild_state()
    raw = await _redis.get(f"wavox:guild:{guild_id}:state")
    if not raw:
        return _empty_guild_state()
    try:
        return _normalize_guild_state(json.loads(raw))
    except json.JSONDecodeError:
        return _empty_guild_state()


def _lyrics_query(track: dict | None) -> str:
    if not isinstance(track, dict):
        return ""
    return str(track.get("title") or "").strip()


async def _fetch_lyrics(q: str) -> dict:
    q = q.strip()
    if not q:
        return {"synced": None, "plain": None}

    cached = _lyrics_cache.get(q)
    if cached and (_time.time() - cached[0]) < LYRICS_CACHE_TTL:
        return cached[1]

    cleaned = q
    for suffix in ['(Official Audio)', '(Official Video)', '(Lyrics)',
                   '(Official Music Video)', '[Official Audio]', '[Official Video]',
                   '(Audio)', '(Video)', '- Topic']:
        cleaned = cleaned.replace(suffix, '')
    cleaned = cleaned.strip()

    result = {"synced": None, "plain": None}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://lrclib.net/api/search",
            params={"q": cleaned},
            timeout=10.0,
        )
        if resp.status_code == 200:
            results = resp.json()
            if results:
                best = results[0]
                result = {
                    "synced": best.get("syncedLyrics"),
                    "plain": best.get("plainLyrics"),
                    "artist": best.get("artistName", ""),
                    "title": best.get("trackName", ""),
                }

    _lyrics_cache[q] = (_time.time(), result)
    return result


# --- User API ---

@app.get("/api/me")
async def api_me(request: Request):
    session = _require_session(request)

    if not _redis:
        raise HTTPException(503, "Backend is not ready")
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
    session = _require_session(request)
    await _require_guild_access(session, guild_id)
    return JSONResponse(await _get_cached_guild_state(guild_id))


@app.post("/api/guilds/{guild_id}/playback")
async def api_playback(guild_id: str, request: Request):
    session = _require_session(request)
    await _require_guild_access(session, guild_id)

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
    session = _require_session(request)

    guild_id = request.query_params.get("guild_id", "")
    if not guild_id:
        raise HTTPException(400, "guild_id required")
    await _require_guild_access(session, guild_id)

    request_id = f"search_{session['user_id']}_{int(_time.time() * 1000)}"
    await _redis.publish("wavox:commands", json.dumps({
        "guild_id": guild_id,
        "action": "search",
        "query": q,
        "user_id": session["user_id"],
        "request_id": request_id,
    }))

    result = await _redis.blpop(f"wavox:response:{request_id}", timeout=10)
    if not result:
        return JSONResponse([])
    return JSONResponse(json.loads(result[1]))


@app.get("/api/lyrics")
async def api_lyrics(q: str, request: Request):
    _require_session(request)
    return JSONResponse(await _fetch_lyrics(q))


@app.get("/api/guilds/{guild_id}/user-status")
async def api_user_status(guild_id: str, request: Request):
    session = _require_session(request)
    await _require_guild_access(session, guild_id)

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


# --- Admin API ---

@app.get("/api/admin/guilds")
async def api_admin_guilds(request: Request):
    """List guilds where the caller has admin rights AND the bot is active."""
    session = _require_session(request)
    if not _redis:
        raise HTTPException(503, "Backend is not ready")
    active = await _redis.smembers("wavox:active_guilds")
    guilds = [
        g for g in session.get("guilds", [])
        if g.get("is_admin") and g["id"] in active
    ]
    return JSONResponse({"guilds": guilds})


@app.get("/api/admin/guilds/{guild_id}/overview")
async def api_admin_overview(guild_id: str, request: Request):
    session = _require_session(request)
    await _require_admin_guild_access(session, guild_id)

    request_id = f"admin_overview_{session['user_id']}_{guild_id}_{int(_time.time() * 1000)}"
    await _redis.publish("wavox:commands", json.dumps({
        "guild_id": guild_id,
        "action": "get_guild_overview",
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
    if not _redis or not await _redis.sismember("wavox:active_guilds", guild_id):
        await websocket.close(code=4003)
        return

    await websocket.accept()

    pubsub = _redis.pubsub()
    await pubsub.subscribe(f"wavox:events:{guild_id}")
    current_lyrics_key = None
    lyrics_task: asyncio.Task | None = None
    send_lock = asyncio.Lock()

    async def send_json(payload: dict):
        async with send_lock:
            await websocket.send_text(json.dumps(payload))

    async def publish_lyrics(lyrics_key: str):
        try:
            lyrics = await _fetch_lyrics(lyrics_key)
            if lyrics_key != current_lyrics_key:
                return

            await send_json({"type": "lyrics_update", "data": lyrics})
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.warning("Lyrics update failed for %s: %s", lyrics_key, e)

    async def send_state_and_related(raw_state: dict | None):
        nonlocal current_lyrics_key, lyrics_task
        state = _normalize_guild_state(raw_state)
        await send_json({"type": "state_update", "data": state})

        lyrics_key = _lyrics_query(state.get("now_playing"))
        if lyrics_key == current_lyrics_key:
            return

        if lyrics_task and not lyrics_task.done():
            lyrics_task.cancel()
            lyrics_task = None

        current_lyrics_key = lyrics_key
        if not lyrics_key:
            await send_json({"type": "lyrics_update", "data": {"synced": None, "plain": None}})
            return

        await send_json({"type": "lyrics_update", "data": {"synced": None, "plain": None}})
        lyrics_task = asyncio.create_task(publish_lyrics(lyrics_key))

    async def redis_reader():
        await send_state_and_related(await _get_cached_guild_state(guild_id))
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            payload = json.loads(message["data"])
            await send_state_and_related(payload)

    async def client_reader():
        while True:
            await websocket.receive()

    try:
        tasks = {
            asyncio.create_task(redis_reader()),
            asyncio.create_task(client_reader()),
        }
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            task.result()
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    finally:
        if lyrics_task and not lyrics_task.done():
            lyrics_task.cancel()
        await pubsub.unsubscribe(f"wavox:events:{guild_id}")
        await pubsub.aclose()


# --- Static site (mkdocs landing) - kept under /docs ---
app.mount("/docs", StaticFiles(directory="/web/site", html=True), name="site")
