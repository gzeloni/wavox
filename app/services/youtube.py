import logging
import time
import asyncio
import yt_dlp as youtube_dl
from utils.config import YDL_OPTS

log = logging.getLogger(__name__)

# URL cache: webpage_url -> (stream_url, info_dict, timestamp)
_url_cache = {}
_CACHE_TTL = 18000  # 5 hours — YouTube URLs expire in ~6h

# Flat opts for fast metadata-only searches (no stream extraction)
_FLAT_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'default_search': 'ytsearch',
    'extract_flat': 'in_playlist',
    'socket_timeout': 10,
}


def _extract_info(yt_query, opts=None):
    with youtube_dl.YoutubeDL(opts or YDL_OPTS) as ydl:
        return ydl.extract_info(yt_query, download=False)


async def _extract_with_timeout(yt_query, timeout=30, opts=None):
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_extract_info, yt_query, opts),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        raise Exception(f"Extraction timed out after {timeout}s")


def _get_best_audio_url(info):
    if 'formats' in info:
        direct_formats = []
        hls_formats = []

        for fmt in info['formats']:
            if fmt.get('acodec') == 'none':
                continue
            url = fmt.get('url', '')
            if not url:
                continue
            if '.m3u8' in url or 'hls' in fmt.get('protocol', ''):
                hls_formats.append(fmt)
            else:
                direct_formats.append(fmt)

        if direct_formats:
            direct_formats.sort(key=lambda f: f.get('abr', 0) or f.get('tbr', 0), reverse=True)
            return direct_formats[0]['url']

        if hls_formats:
            hls_formats.sort(key=lambda f: f.get('abr', 0) or f.get('tbr', 0), reverse=True)
            return hls_formats[0]['url']

    return info.get('url')


def _cache_result(webpage_url, stream_url, info):
    _url_cache[webpage_url] = (stream_url, info, time.time())
    # Evict old entries
    if len(_url_cache) > 500:
        cutoff = time.time() - _CACHE_TTL
        expired = [k for k, v in _url_cache.items() if v[2] < cutoff]
        for k in expired:
            del _url_cache[k]


def _get_cached(webpage_url):
    if webpage_url in _url_cache:
        stream_url, info, ts = _url_cache[webpage_url]
        if time.time() - ts < _CACHE_TTL:
            return stream_url, info
        del _url_cache[webpage_url]
    return None, None


async def search_youtube_fast(query, max_results=5):
    """Fast metadata-only search — no stream URL extraction."""
    try:
        info = await _extract_with_timeout(
            f'ytsearch{max_results}:{query}', timeout=10, opts=_FLAT_OPTS
        )
        if 'entries' not in info:
            return []
        results = []
        for entry in info['entries']:
            if not entry:
                continue
            results.append({
                'title': entry.get('title', 'Unknown'),
                'webpage_url': entry.get('url') or entry.get('webpage_url', ''),
                'duration': entry.get('duration'),
                'channel': entry.get('channel') or entry.get('uploader', ''),
            })
        return results
    except Exception as e:
        log.error("YouTube fast search error: %s", e)
        return []


async def refresh_url(webpage_url):
    try:
        info = await _extract_with_timeout(webpage_url)
        url = _get_best_audio_url(info)
        if url:
            _cache_result(webpage_url, url, info)
            return url
    except Exception as e:
        log.warning("Error refreshing URL: %s", e)
    return None


async def search_youtube(query, max_results=5):
    try:
        info = await _extract_with_timeout(f'ytsearch{max_results}:{query}')
        if 'entries' not in info:
            return []
        results = []
        for entry in info['entries']:
            if not entry:
                continue
            results.append({
                'title': entry.get('title', 'Unknown'),
                'webpage_url': entry.get('webpage_url', ''),
                'duration': entry.get('duration'),
                'thumbnail': entry.get('thumbnail'),
                'channel': entry.get('channel', ''),
            })
        return results
    except Exception as e:
        log.error("YouTube error: %s", e)
        return []


async def resolve_youtube_entry(webpage_url):
    # Check cache first
    cached_url, cached_info = _get_cached(webpage_url)
    if cached_url and cached_info:
        return {
            'url': cached_url,
            'title': cached_info.get('title', 'Unknown'),
            'webpage_url': cached_info.get('webpage_url', webpage_url),
            'duration': cached_info.get('duration'),
            'thumbnail': cached_info.get('thumbnail'),
        }

    try:
        info = await _extract_with_timeout(webpage_url)
        url = _get_best_audio_url(info)
        if not url:
            return None
        wp = info.get('webpage_url', webpage_url)
        _cache_result(wp, url, info)
        return {
            'url': url,
            'title': info['title'],
            'webpage_url': wp,
            'duration': info.get('duration'),
            'thumbnail': info.get('thumbnail'),
        }
    except Exception as e:
        log.error("Error resolving YouTube entry: %s", e)
        return None


async def get_youtube_url(search_query):
    yt_query = (
        f'ytsearch:{search_query}'
        if not search_query.startswith(('http://', 'https://'))
        else search_query
    )

    try:
        info = await _extract_with_timeout(yt_query)

        if 'entries' in info:
            entries = info['entries']

            for entry in entries[:5]:
                if entry:
                    title_lower = entry.get('title', '').lower()
                    channel_lower = entry.get('channel', '').lower()

                    if (
                        any(k in title_lower for k in [
                            'official audio', 'audio', 'lyric'])
                        or 'topic' in channel_lower
                        or 'vevo' in channel_lower
                    ):
                        info = entry
                        break
            else:
                info = entries[0]

        url = _get_best_audio_url(info)

        if not url:
            raise ValueError("No valid stream URL found")

        wp = info.get('webpage_url', yt_query)
        _cache_result(wp, url, info)

        return {
            'url': url,
            'title': info['title'],
            'webpage_url': wp,
            'duration': info.get('duration'),
            'thumbnail': info.get('thumbnail'),
        }

    except Exception as e:
        log.error("YouTube error: %s", e)
        return None
