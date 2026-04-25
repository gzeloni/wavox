import { error, redirect } from '@sveltejs/kit';

import { createSessionData, exchangeDiscordCode, loadDiscordIdentity } from '../../../../server/discord.js';
import {
  clearOauthStateCookie,
  setSessionCookie,
  verifyOauthState
} from '../../../../server/session.js';

export const GET = async ({ cookies, url }) => {
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');

  if (!code || !state) {
    throw error(400, 'OAuth2 callback is invalid');
  }
  if (!verifyOauthState(cookies, state)) {
    throw error(400, 'OAuth2 state is invalid');
  }

  const tokens = await exchangeDiscordCode(code);
  const identity = await loadDiscordIdentity(tokens.access_token);

  clearOauthStateCookie(cookies);
  setSessionCookie(cookies, createSessionData(identity.user, identity.guilds));

  throw redirect(302, '/app');
};
