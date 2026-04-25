import { json } from '@sveltejs/kit';

import { getCachedGuildState } from '../../../../../../server/state.js';
import { requireGuildAccess, requireSession } from '$lib/server/api';

export const GET = async (event) => {
  const session = requireSession(event);
  const guildId = event.params.guildId;

  await requireGuildAccess(session, guildId);
  return json(await getCachedGuildState(guildId));
};
