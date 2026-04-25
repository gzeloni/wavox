import type {
  Me,
  SearchResult,
  UserStats,
  GuildOverview,
  PlaybackAction,
  Guild
} from './types';

async function http<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: 'same-origin', ...init });
  if (res.status === 401) throw new UnauthorizedError();
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

export class UnauthorizedError extends Error {
  constructor() {
    super('unauthorized');
  }
}

export const api = {
  me: () => http<Me>('/api/me'),

  playback: (guildId: string, action: PlaybackAction, extra: Record<string, unknown> = {}) =>
    http<{ ok: boolean }>(`/api/guilds/${guildId}/playback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, ...extra })
    }),

  search: (guildId: string, q: string) =>
    http<SearchResult[]>(`/api/search?q=${encodeURIComponent(q)}&guild_id=${guildId}`),

  userStatus: (guildId: string) => http<UserStats | Record<string, never>>(`/api/guilds/${guildId}/user-status`),

  adminGuilds: () => http<{ guilds: Guild[] }>('/api/admin/guilds'),

  adminOverview: (guildId: string) =>
    http<GuildOverview | Record<string, never>>(`/api/admin/guilds/${guildId}/overview`)
};
