export function fmtTime(s: number | null | undefined): string {
  if (s == null) return '0:00';
  const i = Math.floor(s);
  const m = Math.floor(i / 60);
  return `${m}:${String(i % 60).padStart(2, '0')}`;
}

export function guildInitials(name: string): string {
  return name
    .split(/\s+/)
    .map((w) => w[0] ?? '')
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

export function avatarUrl(userId: string, hash: string | null, size = 64): string | null {
  if (!hash) return null;
  return `https://cdn.discordapp.com/avatars/${userId}/${hash}.png?size=${size}`;
}

export function guildIconUrl(guildId: string, hash: string | null, size = 64): string | null {
  if (!hash) return null;
  return `https://cdn.discordapp.com/icons/${guildId}/${hash}.png?size=${size}`;
}

export interface LRCLine {
  time: number;
  text: string;
}

export function parseLRC(text: string): LRCLine[] {
  const lines: LRCLine[] = [];
  for (const raw of text.split('\n')) {
    const match = raw.match(/^\[(\d{2}):(\d{2})\.(\d{2,3})\]\s*(.*)/);
    if (match) {
      const mins = parseInt(match[1]);
      const secs = parseInt(match[2]);
      const ms = parseInt(match[3].padEnd(3, '0'));
      lines.push({
        time: mins * 60 + secs + ms / 1000,
        text: match[4] || '\u00A0'
      });
    }
  }
  return lines;
}
