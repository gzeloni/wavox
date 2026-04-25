import { LYRICS_CACHE_TTL } from './config.js';

const lyricsCache = new Map();

export function lyricsQuery(track) {
  if (!track || typeof track !== 'object') return '';
  return String(track.title || '').trim();
}

function cleanQuery(query) {
  let cleaned = query.trim();
  for (const suffix of [
    '(Official Audio)',
    '(Official Video)',
    '(Lyrics)',
    '(Official Music Video)',
    '[Official Audio]',
    '[Official Video]',
    '(Audio)',
    '(Video)',
    '- Topic'
  ]) {
    cleaned = cleaned.replace(suffix, '');
  }
  return cleaned.trim();
}

export async function fetchLyrics(query, signal) {
  const normalizedQuery = query.trim();
  if (!normalizedQuery) {
    return { synced: null, plain: null };
  }

  const cached = lyricsCache.get(normalizedQuery);
  if (cached && Date.now() - cached.timestamp < LYRICS_CACHE_TTL * 1000) {
    return cached.value;
  }

  const response = await fetch(`https://lrclib.net/api/search?q=${encodeURIComponent(cleanQuery(normalizedQuery))}`, {
    signal
  });

  let lyrics = { synced: null, plain: null };
  if (response.ok) {
    const results = await response.json();
    if (Array.isArray(results) && results.length > 0) {
      const best = results[0];
      lyrics = {
        synced: best.syncedLyrics || null,
        plain: best.plainLyrics || null,
        artist: best.artistName || '',
        title: best.trackName || ''
      };
    }
  }

  lyricsCache.set(normalizedQuery, {
    timestamp: Date.now(),
    value: lyrics
  });

  return lyrics;
}
