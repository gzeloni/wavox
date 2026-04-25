const webOrigin = process.env.WEB_ORIGIN || '';
const secureDefault = webOrigin.startsWith('https://') ? 'true' : 'false';
const secureValue = (process.env.WEB_COOKIE_SECURE || secureDefault).toLowerCase();

export const DISCORD_CLIENT_ID = process.env.DISCORD__CLIENT_ID || '';
export const DISCORD_CLIENT_SECRET = process.env.DISCORD__CLIENT_SECRET || '';
export const DISCORD_REDIRECT_URI = process.env.DISCORD__REDIRECT_URI || '';
export const SECRET_KEY = process.env.WEB_SECRET_KEY || 'wavox-change-me-in-prod';
export const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379/0';
export const WEB_ORIGIN = webOrigin;

export const SESSION_MAX_AGE = 86400;
export const OAUTH_STATE_MAX_AGE = 600;
export const COOKIE_SECURE = ['1', 'true', 'yes', 'on'].includes(secureValue);

export const PERM_ADMINISTRATOR = 0x8;
export const PERM_MANAGE_GUILD = 0x20;

export const DISCORD_AUTH_URL = 'https://discord.com/api/oauth2/authorize';
export const DISCORD_TOKEN_URL = 'https://discord.com/api/oauth2/token';
export const DISCORD_API = 'https://discord.com/api/v10';

export const SESSION_COOKIE_NAME = 'wavox_session';
export const OAUTH_STATE_COOKIE_NAME = 'wavox_oauth_state';

export const LYRICS_CACHE_TTL = 3600;
