import logging
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from services.youtube import get_youtube_url
from services.music import add_to_queue
from utils.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_MARKET, MAX_PLAYLIST_TRACKS


log = logging.getLogger(__name__)

sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))


def _format_track(track):
    artist = track.get('artists', [{}])[0].get('name', 'Unknown')
    name = track.get('name', 'Unknown')
    title = f"{artist} - {name}"
    duration = None
    if track.get('duration_ms'):
        duration = track['duration_ms'] // 1000
    images = track.get('album', {}).get('images', [])
    thumbnail = images[0]['url'] if images else None
    return {
        'title': title,
        'search_query': title,
        'duration': duration,
        'thumbnail': thumbnail,
    }


async def get_spotify_track(track_id):
    if not sp:
        return None
    try:
        track = await asyncio.to_thread(sp.track, track_id, market=SPOTIFY_MARKET)
        return _format_track(track)
    except Exception as e:
        log.error("Error fetching Spotify track: %s", e)
        return None


def _extract_tracks(items):
    tracks = []
    for item in items:
        track = item.get('track') if 'track' in item else item
        if track:
            tracks.append(_format_track(track))
    return tracks


async def get_spotify_playlist(playlist_id):
    if not sp:
        return []
    try:
        tracks = []
        offset = 0
        while True:
            results = await asyncio.to_thread(
                sp.playlist_items, playlist_id, limit=100, offset=offset, market=SPOTIFY_MARKET
            )
            tracks.extend(_extract_tracks(results['items']))
            if not results['next']:
                break
            offset += 100

        log.info("Loaded %d tracks from playlist", len(tracks))
        return tracks
    except Exception as e:
        log.error("Error fetching Spotify playlist %s: %s", playlist_id, e)
        return []


async def get_spotify_album(album_id):
    if not sp:
        return []
    try:
        results = await asyncio.to_thread(sp.album_tracks, album_id, limit=50, market=SPOTIFY_MARKET)
        tracks = _extract_tracks(results['items'])

        while results['next']:
            results = await asyncio.to_thread(sp.next, results)
            tracks.extend(_extract_tracks(results['items']))

        log.info("Loaded %d tracks from album", len(tracks))
        return tracks
    except Exception as e:
        log.error("Error fetching Spotify album %s: %s", album_id, e)
        return []


async def _resolve_track(track, sem):
    async with sem:
        try:
            youtube_info = await get_youtube_url(track['search_query'])
            if youtube_info:
                return {
                    'url': youtube_info['url'],
                    'title': track['title'],
                    'webpage_url': youtube_info.get('webpage_url'),
                    'duration': track.get('duration') or youtube_info.get('duration'),
                    'thumbnail': track.get('thumbnail') or youtube_info.get('thumbnail'),
                }
        except Exception as e:
            log.warning("Error processing track %s: %s", track['title'], e)
        return None


async def process_spotify_tracks(tracks, guild_id, channel, user_id=0):
    max_tracks = min(MAX_PLAYLIST_TRACKS, len(tracks))
    sem = asyncio.Semaphore(10)

    results = await asyncio.gather(
        *[_resolve_track(t, sem) for t in tracks[:max_tracks]],
        return_exceptions=True
    )

    processed = 0
    failed = 0
    for result in results:
        if isinstance(result, Exception) or result is None:
            failed += 1
        else:
            result['requested_by'] = user_id
            add_to_queue(guild_id, result)
            processed += 1

    if processed > 0 or failed > 0:
        status = f"✅ {processed} tracks added to queue"
        if failed > 0:
            status += f" ({failed} failed)"
        await channel.send(status, delete_after=10)
