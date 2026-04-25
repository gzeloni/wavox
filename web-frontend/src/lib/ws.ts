import type { GuildSocketMessage } from './types';

type MessageHandler = (message: GuildSocketMessage) => void;

export class GuildSocket {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private closed = false;
  private reconnectAttempts = 0;

  constructor(
    private guildId: string,
    private onMessage: MessageHandler
  ) {}

  connect() {
    if (this.closed) return;
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.ws = new WebSocket(`${proto}//${location.host}/api/guilds/${this.guildId}/ws`);
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
    };
    this.ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'state_update' || msg.type === 'lyrics_update') {
          this.onMessage(msg as GuildSocketMessage);
        }
      } catch {
        /* ignore */
      }
    };
    this.ws.onclose = (event) => {
      if (this.closed) return;
      if (event.code === 4003 || event.code === 1008) return;
      this.reconnectAttempts += 1;
      const delay = Math.min(30000, 1000 * 2 ** Math.min(this.reconnectAttempts, 5));
      const jitter = Math.floor(Math.random() * 500);
      this.reconnectTimer = setTimeout(() => this.connect(), delay + jitter);
    };
  }

  close() {
    this.closed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }
}
