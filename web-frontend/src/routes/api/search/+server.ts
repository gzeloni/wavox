import { error, json } from '@sveltejs/kit';

import { publishCommandAndWait } from '../../../../server/commands.js';
import { requireGuildAccess, requireSession } from '$lib/server/api';

export const GET = async (event) => {
  const session = requireSession(event);
  const query = event.url.searchParams.get('q') || '';
  const guildId = event.url.searchParams.get('guild_id') || '';

  if (!guildId) {
    throw error(400, 'guild_id required');
  }

  await requireGuildAccess(session, guildId);

  const requestId = `search_${session.user_id}_${Date.now()}`;
  const results = await publishCommandAndWait(
    {
      guild_id: guildId,
      action: 'search',
      query,
      user_id: session.user_id,
      request_id: requestId
    },
    `wavox:response:${requestId}`,
    10
  );

  return json(results || []);
};
