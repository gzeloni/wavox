import { json } from '@sveltejs/kit';

import { activeGuildsForSession, requireSession } from '$lib/server/api';

export const GET = async (event) => {
  const session = requireSession(event);
  const guilds = (await activeGuildsForSession(session)).filter((guild) => guild.is_admin);
  return json({ guilds });
};
