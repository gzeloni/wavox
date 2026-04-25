import { redirect } from '@sveltejs/kit';

import { buildLoginUrl } from '../../../../server/discord.js';
import { createOauthState, setOauthStateCookie } from '../../../../server/session.js';

export const GET = async ({ cookies }) => {
  const state = createOauthState();
  setOauthStateCookie(cookies, state);
  throw redirect(302, buildLoginUrl(state));
};
