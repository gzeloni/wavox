import {
  DISCORD_API,
  DISCORD_AUTH_URL,
  DISCORD_CLIENT_ID,
  DISCORD_CLIENT_SECRET,
  DISCORD_REDIRECT_URI,
  DISCORD_TOKEN_URL,
  PERM_ADMINISTRATOR,
  PERM_MANAGE_GUILD
} from './config.js';

function ensureDiscordOAuth() {
  if (!DISCORD_CLIENT_ID || !DISCORD_CLIENT_SECRET || !DISCORD_REDIRECT_URI) {
    throw new Error('Discord OAuth2 is not configured');
  }
}

export function buildLoginUrl(state) {
  ensureDiscordOAuth();

  const params = new URLSearchParams({
    client_id: DISCORD_CLIENT_ID,
    redirect_uri: DISCORD_REDIRECT_URI,
    response_type: 'code',
    scope: 'identify guilds',
    state
  });

  return `${DISCORD_AUTH_URL}?${params.toString()}`;
}

export function isGuildAdmin(guild) {
  if (guild.owner) return true;

  const permissions = Number(guild.permissions || 0);
  if (!Number.isFinite(permissions)) return false;

  return Boolean(permissions & (PERM_ADMINISTRATOR | PERM_MANAGE_GUILD));
}

export async function exchangeDiscordCode(code) {
  ensureDiscordOAuth();

  const response = await fetch(DISCORD_TOKEN_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams({
      client_id: DISCORD_CLIENT_ID,
      client_secret: DISCORD_CLIENT_SECRET,
      grant_type: 'authorization_code',
      code,
      redirect_uri: DISCORD_REDIRECT_URI
    })
  });

  if (!response.ok) {
    throw new Error('OAuth2 token exchange failed');
  }

  return response.json();
}

async function discordGet(path, accessToken) {
  const response = await fetch(`${DISCORD_API}${path}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`
    }
  });

  if (!response.ok) {
    throw new Error(`Discord API request failed for ${path}`);
  }

  return response.json();
}

export async function loadDiscordIdentity(accessToken) {
  const [user, guilds] = await Promise.all([
    discordGet('/users/@me', accessToken),
    discordGet('/users/@me/guilds', accessToken)
  ]);

  return {
    user,
    guilds
  };
}

export function createSessionData(user, guilds) {
  return {
    user_id: user.id,
    username: user.username,
    avatar: user.avatar || null,
    guilds: guilds.map((guild) => ({
      id: guild.id,
      name: guild.name,
      icon: guild.icon || null,
      is_admin: isGuildAdmin(guild)
    }))
  };
}
