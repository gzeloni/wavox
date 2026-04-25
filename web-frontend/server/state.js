import { getRedis } from './redis.js';

export function emptyGuildState() {
  return {
    now_playing: null,
    queue: [],
    is_playing: false,
    is_paused: false,
    loop_mode: 'off'
  };
}

export function normalizeGuildState(rawState) {
  if (!rawState || typeof rawState !== 'object') {
    return emptyGuildState();
  }

  const state = rawState.data && typeof rawState.data === 'object' ? rawState.data : rawState;
  if (!state || typeof state !== 'object') {
    return emptyGuildState();
  }

  const normalized = emptyGuildState();
  const nowPlaying = state.now_playing;
  if (nowPlaying && typeof nowPlaying === 'object') {
    normalized.now_playing = {
      title: nowPlaying.title || null,
      thumbnail: nowPlaying.thumbnail || null,
      webpage_url: nowPlaying.webpage_url || null,
      duration: nowPlaying.duration || null,
      started_at: nowPlaying.started_at || 0,
      offset: nowPlaying.offset || 0,
      paused_at: nowPlaying.paused_at || null,
      elapsed: nowPlaying.elapsed || 0
    };
  }

  if (Array.isArray(state.queue)) {
    normalized.queue = state.queue
      .filter((item) => item && typeof item === 'object')
      .map((item) => ({
        title: item.title || null,
        duration: item.duration || null
      }));
  }

  normalized.is_playing = Boolean(state.is_playing);
  normalized.is_paused = Boolean(state.is_paused);
  if (['off', 'track', 'queue'].includes(state.loop_mode)) {
    normalized.loop_mode = state.loop_mode;
  }

  return normalized;
}

export function guildIds(session) {
  return Array.isArray(session?.guilds) ? session.guilds.map((guild) => guild.id) : [];
}

export function adminGuildIds(session) {
  return Array.isArray(session?.guilds)
    ? session.guilds.filter((guild) => guild.is_admin).map((guild) => guild.id)
    : [];
}

export async function isGuildActive(guildId) {
  const redis = await getRedis();
  return redis.sIsMember('wavox:active_guilds', guildId);
}

export async function getActiveGuilds() {
  const redis = await getRedis();
  return redis.sMembers('wavox:active_guilds');
}

export async function getCachedGuildState(guildId) {
  const redis = await getRedis();
  const raw = await redis.get(`wavox:guild:${guildId}:state`);
  if (!raw) {
    return emptyGuildState();
  }

  try {
    return normalizeGuildState(JSON.parse(raw));
  } catch {
    return emptyGuildState();
  }
}
