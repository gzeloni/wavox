import { writable, derived } from 'svelte/store';
import type { GuildState, LyricsResponse } from '$lib/types';
import { GuildSocket } from '$lib/ws';

export const guildId = writable<string | null>(null);
export const state = writable<GuildState | null>(null);
export const lyrics = writable<LyricsResponse | null>(null);

let socket: GuildSocket | null = null;

function storageKey(id: string) {
  return `wavox:${id}`;
}

function loadCache(id: string): GuildState | null {
  try {
    const raw = localStorage.getItem(storageKey(id));
    return raw ? (JSON.parse(raw) as GuildState) : null;
  } catch {
    return null;
  }
}

function saveCache(id: string, s: GuildState) {
  try {
    localStorage.setItem(storageKey(id), JSON.stringify(s));
  } catch {
    /* ignore */
  }
}

export function selectGuild(id: string) {
  guildId.set(id);
  lyrics.set(null);

  const cached = loadCache(id);
  if (cached) state.set(cached);

  connectWS(id);
}

export function disconnectGuild() {
  socket?.close();
  socket = null;
  guildId.set(null);
  state.set(null);
  lyrics.set(null);
}

function connectWS(id: string) {
  socket?.close();
  socket = new GuildSocket(id, (message) => {
    if (message.type === 'state_update') {
      state.set(message.data);
      saveCache(id, message.data);
    } else if (message.type === 'lyrics_update') {
      lyrics.set(message.data);
    }
  });
  socket.connect();
}

export const elapsed = derived(state, ($state) => {
  if (!$state || !$state.now_playing) return 0;
  return $state.now_playing.elapsed || 0;
});
