import { json } from '@sveltejs/kit';

import { activeGuildsForSession, requireSession } from '$lib/server/api';

export const GET = async (event) => {
  const session = requireSession(event);
  const guilds = await activeGuildsForSession(session);

  return json({
    user_id: session.user_id,
    username: session.username,
    avatar: session.avatar || null,
    guilds
  });
};
