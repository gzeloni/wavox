import { json } from '@sveltejs/kit';

import { publishCommandAndWait } from '../../../../../../server/commands.js';
import { requireGuildAccess, requireSession } from '$lib/server/api';

export const GET = async (event) => {
  const session = requireSession(event);
  const guildId = event.params.guildId;

  await requireGuildAccess(session, guildId);

  const requestId = `status_${session.user_id}_${guildId}_${Date.now()}`;
  const result = await publishCommandAndWait(
    {
      guild_id: guildId,
      action: 'get_user_status',
      user_id: session.user_id,
      request_id: requestId
    },
    `wavox:response:${requestId}`,
    5
  );

  return json(result || {});
};
