export interface Guild {
  id: string;
  name: string;
  icon: string | null;
  is_admin?: boolean;
}

export interface Me {
  user_id: string;
  username: string;
  avatar: string | null;
  guilds: Guild[];
}

export interface NowPlaying {
  title: string | null;
  thumbnail: string | null;
  webpage_url: string | null;
  duration: number | null;
  started_at: number;
  offset: number;
  paused_at: number | null;
  elapsed: number;
}

export interface QueueItem {
  title: string | null;
  duration: number | null;
}

export type LoopMode = 'off' | 'track' | 'queue';

export interface GuildState {
  now_playing: NowPlaying | null;
  queue: QueueItem[];
  is_playing: boolean;
  is_paused: boolean;
  loop_mode: LoopMode;
}

export interface SearchResult {
  title: string;
  url: string;
  duration: number | null;
  channel: string;
  source: 'youtube' | 'spotify' | 'soundcloud';
}

export interface LyricsResponse {
  synced: string | null;
  plain: string | null;
  artist?: string;
  title?: string;
}

export type GuildSocketMessage =
  | { type: 'state_update'; data: GuildState }
  | { type: 'lyrics_update'; data: LyricsResponse };

export interface UserStats {
  total_plays: number;
  total_skips: number;
  total_likes: number;
  skip_rate: number;
  like_rate: number;
  repeat_rate: number;
  top_tracks: Array<{ title: string; plays: number }>;
  top_artists: Array<{ artist: string; plays: number }>;
  hour_blocks: number[];
}

export interface GuildOverview {
  guild_name: string | null;
  member_count: number | null;
  voice_connected: boolean;
  voice_channel: string | null;
  is_playing: boolean;
  queue_size: number;
  loop_mode: LoopMode;
  recent: Array<{ title: string; user_id: string | null; played_at: string }>;
  top_tracks: Array<{ title: string; plays: number }>;
  most_active: Array<{ user_id: string | null; plays: number }>;
}

export type PlaybackAction =
  | 'pause'
  | 'resume'
  | 'skip'
  | 'previous'
  | 'shuffle'
  | 'loop'
  | 'goto'
  | 'stop'
  | 'clear'
  | 'play'
  | 'skip_to';
