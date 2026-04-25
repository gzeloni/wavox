# Architecture

## System Components

Wavox is composed of four primary services:

| Component | Responsibility |
|---|---|
| `discord-bot` | Executes commands, manages guild voice sessions, resolves tracks, and controls playback |
| `web` | Hosts OAuth, sessions, REST APIs, admin endpoints, lyrics lookups, and WebSocket connections |
| `web-frontend` | Provides the dashboard UI in SvelteKit |
| `redis` | Carries commands and state events between backend services |

## Data Flow

### Playback Flow

1. A Discord user issues `/play` or a text command.
2. The bot validates the voice state and resolves the query:
   - YouTube search or URL through `yt-dlp`
   - Spotify track/album/playlist through Spotify APIs plus YouTube resolution
3. The playback engine creates an FFmpeg source and streams audio to Discord.
4. The bot writes playback state updates to Redis.
5. The web backend relays normalized state to dashboard clients through WebSockets.

### Dashboard Flow

1. A browser authenticates through Discord OAuth.
2. FastAPI stores a signed session cookie.
3. The SvelteKit frontend requests guild data and opens a guild-specific WebSocket.
4. FastAPI subscribes to Redis events for that guild.
5. The frontend receives:
   - `state_update` messages for queue and playback state
   - `lyrics_update` messages when the current track changes

## Backend Modules

### `app/bot/`

- `client.py`: bot bootstrap and lifecycle hooks
- `cogs/music.py`: playback and queue commands
- `cogs/utility.py`: ping, clip, download, and lyrics commands
- `cogs/stats.py`: play history and listening analytics commands

### `app/services/`

- `music.py`: guild player state machine, playback offsets, queue handling
- `message_bus.py`: Redis publisher/consumer and real-time state broadcasting
- `youtube.py`: YouTube search, metadata extraction, and playable URL resolution
- `spotify.py`: Spotify intake and track expansion
- `database.py`: SQLite schema and analytics queries

### `web/`

- `server.py`: FastAPI application for API, OAuth, sessions, WebSockets, and lyrics transport
- `docs/`: MkDocs content for the public documentation pages

### `web-frontend/`

- `src/lib/components/`: dashboard UI components
- `src/lib/stores/`: reactive state for sessions, playback, and lyrics
- `src/lib/ws.ts`: guild-scoped WebSocket client
- `src/routes/`: application, dashboard redirect, landing, and admin pages

## State and Persistence

### Redis

Redis is used for:

- command dispatch from the web backend to the bot
- guild-scoped playback state fan-out
- active guild registration
- short-lived cached state per guild

### SQLite

SQLite is used for:

- play history
- user interaction events such as likes and skips
- 30-day user analytics
- guild-level recent tracks and activity summaries

## Real-Time Playback Model

The playback engine tracks:

- `playback_start_time`
- `playback_offset`
- `pause_time`
- queue state
- loop mode

The message bus periodically emits normalized playback snapshots. The frontend renders only what the backend sends, which keeps the dashboard aligned with the actual server-side player state.

## Deployment Shape

The expected deployment model is:

1. Docker Compose runs `discord-bot`, `web`, `web-frontend`, and `redis`
2. A reverse proxy exposes the frontend publicly
3. The proxy forwards `/api/*` and OAuth routes to FastAPI
4. The frontend remains the public browser-facing entrypoint
