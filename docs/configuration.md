# Configuration

## Environment Variables

The project reads configuration from the root `.env` file when started through Docker Compose.

## Core Discord Settings

| Variable | Required | Description |
|---|---|---|
| `DISCORD__TOKEN` | Yes | Discord bot token used by `app/main.py` |
| `DISCORD__CLIENT_ID` | Yes for dashboard | Discord OAuth application client ID |
| `DISCORD__CLIENT_SECRET` | Yes for dashboard | Discord OAuth application client secret |
| `DISCORD__REDIRECT_URI` | Yes for dashboard | OAuth callback URL handled by FastAPI |

## Web Session Settings

| Variable | Required | Description |
|---|---|---|
| `WEB_SECRET_KEY` | Yes in production | Signing secret for session and OAuth state cookies |
| `WEB_ORIGIN` | Recommended | Public frontend origin used to infer secure cookie defaults |
| `WEB_COOKIE_SECURE` | Optional | Overrides automatic secure-cookie detection |

## Media and Catalog Settings

| Variable | Required | Description |
|---|---|---|
| `SPOTIFY_CLIENT_ID` | Optional | Enables Spotify resolution |
| `SPOTIFY_CLIENT_SECRET` | Optional | Enables Spotify resolution |
| `SPOTIFY_MARKET` | Optional | Spotify market code, defaults to `US` |

## Infrastructure Settings

| Variable | Required | Description |
|---|---|---|
| `REDIS_URL` | Optional | Redis connection string, defaults to `redis://redis:6379/0` |
| `DB_PATH` | Optional | SQLite path, defaults to `/app/data/history.db` |

## Root `.env` Example

```bash
DISCORD__TOKEN=your_discord_bot_token_here

DISCORD__CLIENT_ID=your_discord_client_id
DISCORD__CLIENT_SECRET=your_discord_client_secret
DISCORD__REDIRECT_URI=http://localhost:3500/dashboard/callback

WEB_SECRET_KEY=replace_this_with_a_long_random_secret
WEB_ORIGIN=http://localhost:3000
WEB_COOKIE_SECURE=false

SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_MARKET=US

REDIS_URL=redis://redis:6379/0
DB_PATH=/app/data/history.db
```

## Service Ports

| Service | Default Port |
|---|---|
| `web-frontend` | `3000` |
| `web` | `3500` |
| `redis` | internal |

## Deployment Notes

- In production, place a reverse proxy in front of the frontend and API
- Make sure the OAuth redirect URI exactly matches the public callback URL
- Use a strong `WEB_SECRET_KEY`
- Set `WEB_COOKIE_SECURE=true` when serving over HTTPS
- Persist the SQLite database and Redis data volumes if you need durable history

## Operational Commands

### Build and start

```bash
make deploy
```

### Build only

```bash
make build
```

### Start existing images

```bash
make run
```

### Stop and remove local images

```bash
make clean
```
