import { error } from '@sveltejs/kit';

import { adminGuildIds, getActiveGuilds, guildIds, isGuildActive } from '../../../server/state.js';
import { getSessionFromCookies } from '../../../server/session.js';

import type { RequestEvent } from '@sveltejs/kit';

export function requireSession(event: RequestEvent) {
  const session = getSessionFromCookies(event.cookies);
  if (!session) {
    throw error(401, 'Unauthorized');
  }
  return session;
}

export async function requireGuildAccess(session: { guilds?: Array<{ id: string }> }, guildId: string) {
  if (!guildIds(session).includes(guildId)) {
    throw error(403, 'Not a member of this guild');
  }
  if (!(await isGuildActive(guildId))) {
    throw error(403, 'Bot is not active in this guild');
  }
}

export async function requireAdminGuildAccess(
  session: { guilds?: Array<{ id: string; is_admin?: boolean }> },
  guildId: string
) {
  if (!adminGuildIds(session).includes(guildId)) {
    throw error(403, 'Admin access required for this guild');
  }
  if (!(await isGuildActive(guildId))) {
    throw error(403, 'Bot is not active in this guild');
  }
}

export async function activeGuildsForSession(session: { guilds?: Array<{ id: string }> }) {
  const active = new Set(await getActiveGuilds());
  return Array.isArray(session.guilds) ? session.guilds.filter((guild) => active.has(guild.id)) : [];
}
