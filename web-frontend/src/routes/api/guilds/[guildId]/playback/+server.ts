import { error, json } from '@sveltejs/kit';

import { publishCommand } from '../../../../../../server/commands.js';
import { requireGuildAccess, requireSession } from '$lib/server/api';

const validActions = new Set([
  'pause',
  'resume',
  'skip',
  'previous',
  'shuffle',
  'loop',
  'goto',
  'stop',
  'clear',
  'play',
  'skip_to'
]);

export const POST = async (event) => {
  const session = requireSession(event);
  const guildId = event.params.guildId;

  await requireGuildAccess(session, guildId);

  const body = await event.request.json();
  const action = typeof body.action === 'string' ? body.action : '';
  if (!validActions.has(action)) {
    throw error(400, 'Invalid action');
  }

  const command: Record<string, unknown> = {
    guild_id: guildId,
    action,
    user_id: session.user_id
  };

  if (action === 'goto') {
    command.position = body.position ?? '0';
  } else if (action === 'skip_to') {
    command.position = body.position ?? 1;
  } else if (action === 'play') {
    command.query = body.query ?? '';
  }

  await publishCommand(command);
  return json({ ok: true });
};
