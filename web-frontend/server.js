import { createServer } from 'node:http';

import { handler } from './build/handler.js';
import { WebSocketServer } from 'ws';

import { extractGuildIdFromPath, handleGuildSocket } from './server/websocket.js';

const host = process.env.HOST || '0.0.0.0';
const port = Number(process.env.PORT || 3000);

const httpServer = createServer((request, response) => {
  handler(request, response);
});

const websocketServer = new WebSocketServer({ noServer: true });

httpServer.on('upgrade', (request, socket, head) => {
  const guildId = extractGuildIdFromPath(request.url, request.headers.host);
  if (!guildId) {
    socket.destroy();
    return;
  }

  websocketServer.handleUpgrade(request, socket, head, (ws) => {
    handleGuildSocket(ws, request, guildId).catch((error) => {
      console.error('Guild WebSocket failed:', error);
      ws.close(1011, 'Internal error');
    });
  });
});

httpServer.listen(port, host, () => {
  console.log(`Wavox frontend listening on http://${host}:${port}`);
});
