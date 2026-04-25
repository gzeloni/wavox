import { json } from '@sveltejs/kit';

import { fetchLyrics } from '../../../../server/lyrics.js';
import { requireSession } from '$lib/server/api';

export const GET = async (event) => {
  requireSession(event);
  try {
    return json(await fetchLyrics(event.url.searchParams.get('q') || ''));
  } catch {
    return json({ synced: null, plain: null });
  }
};
