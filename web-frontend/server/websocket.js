import { createRedisDuplicate, getRedis } from './redis.js';
import { fetchLyrics, lyricsQuery } from './lyrics.js';
import { getSessionFromCookieHeader } from './session.js';
import { getCachedGuildState, guildIds, normalizeGuildState } from './state.js';

const WS_OPEN = 1;

export function extractGuildIdFromPath(requestUrl, host) {
  if (!requestUrl) return null;

  const url = new URL(requestUrl, `http://${host || 'localhost'}`);
  const match = url.pathname.match(/^\/api\/guilds\/([^/]+)\/ws$/);
  return match ? decodeURIComponent(match[1]) : null;
}

function sendJson(ws, payload) {
  return new Promise((resolve, reject) => {
    if (ws.readyState !== WS_OPEN) {
      resolve();
      return;
    }

    ws.send(JSON.stringify(payload), (error) => {
      if (error) {
        reject(error);
      } else {
        resolve();
      }
    });
  });
}

export async function handleGuildSocket(ws, request, guildId) {
  const session = getSessionFromCookieHeader(request.headers.cookie || '');
  if (!session || !guildIds(session).includes(guildId)) {
    ws.close(4003, 'Unauthorized');
    return;
  }

  const redis = await getRedis();
  if (!(await redis.sIsMember('wavox:active_guilds', guildId))) {
    ws.close(4003, 'Inactive guild');
    return;
  }

  const pubsub = await createRedisDuplicate();
  const channel = `wavox:events:${guildId}`;

  let closed = false;
  let currentLyricsKey = null;
  let lyricsController = null;
  let sendQueue = Promise.resolve();
  let socketQueue = Promise.resolve();

  async function cleanup() {
    if (closed) return;
    closed = true;

    if (lyricsController) {
      lyricsController.abort();
      lyricsController = null;
    }

    try {
      await pubsub.unsubscribe(channel);
    } catch {
      /* ignore */
    }

    try {
      await pubsub.quit();
    } catch {
      /* ignore */
    }
  }

  function queueSend(task) {
    sendQueue = sendQueue
      .then(task)
      .catch((error) => {
        if (!closed) {
          console.warn('WebSocket state delivery failed:', error);
        }
      });
  }

  function queueSocketPayload(payload) {
    socketQueue = socketQueue
      .then(() => sendJson(ws, payload))
      .catch((error) => {
        if (!closed) {
          console.warn('WebSocket send failed:', error);
        }
      });

    return socketQueue;
  }

  function publishLyrics(nextLyricsKey) {
    if (lyricsController) {
      lyricsController.abort();
    }

    if (!nextLyricsKey) {
      currentLyricsKey = null;
      queueSocketPayload({ type: 'lyrics_update', data: { synced: null, plain: null } });
      return;
    }

    currentLyricsKey = nextLyricsKey;
    queueSocketPayload({ type: 'lyrics_update', data: { synced: null, plain: null } });

    const controller = new AbortController();
    lyricsController = controller;

    fetchLyrics(nextLyricsKey, controller.signal)
      .then((lyrics) => {
        if (closed || controller.signal.aborted || nextLyricsKey !== currentLyricsKey) {
          return;
        }

        queueSocketPayload({ type: 'lyrics_update', data: lyrics });
      })
      .catch((error) => {
        if (error?.name !== 'AbortError' && !closed) {
          console.warn(`Lyrics update failed for ${nextLyricsKey}:`, error);
        }
      });
  }

  async function sendState(rawState) {
    const state = normalizeGuildState(rawState);
    await queueSocketPayload({ type: 'state_update', data: state });

    const nextLyricsKey = lyricsQuery(state.now_playing);
    if (nextLyricsKey === currentLyricsKey) {
      return;
    }

    publishLyrics(nextLyricsKey);
  }

  ws.on('close', cleanup);
  ws.on('error', cleanup);
  ws.on('message', () => {});

  await pubsub.subscribe(channel, (message) => {
    let payload = null;
    try {
      payload = JSON.parse(message);
    } catch {
      payload = null;
    }

    queueSend(() => sendState(payload));
  });

  queueSend(async () => {
    await sendState(await getCachedGuildState(guildId));
  });
}
