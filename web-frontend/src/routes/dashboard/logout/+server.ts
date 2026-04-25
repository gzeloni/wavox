import { redirect } from '@sveltejs/kit';

import { clearOauthStateCookie, clearSessionCookie } from '../../../../server/session.js';

export const GET = async ({ cookies }) => {
  clearSessionCookie(cookies);
  clearOauthStateCookie(cookies);
  throw redirect(302, '/');
};
