<script lang="ts">
  import { api } from '$lib/api';
  import { guildId } from '$lib/stores/player';
  import { fmtTime } from '$lib/utils';
  import type { SearchResult } from '$lib/types';

  let query = '';
  let suggestions: SearchResult[] = [];
  let open = false;
  let loading = false;
  let timer: ReturnType<typeof setTimeout> | null = null;

  async function fetchSuggestions(q: string) {
    const id = $guildId;
    if (!id || q.length < 2 || q.startsWith('http://') || q.startsWith('https://')) {
      close();
      return;
    }
    loading = true;
    open = true;
    try {
      suggestions = await api.search(id, q);
    } catch {
      suggestions = [];
    }
    loading = false;
  }

  function onInput() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fetchSuggestions(query.trim()), 400);
  }

  function close() {
    open = false;
    suggestions = [];
  }

  async function play(q: string) {
    const id = $guildId;
    if (!id || !q) return;
    await api.playback(id, 'play', { query: q });
    query = '';
    close();
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') play(query.trim());
    if (e.key === 'Escape') close();
  }

  function handleDocClick(e: MouseEvent) {
    if (!(e.target as HTMLElement).closest('.search-shell')) close();
  }
</script>

<svelte:window on:click={handleDocClick} />

<section class="search-shell">
  <div class="search-head">
    <div class="search-kicker">Command Input</div>
    <p>Add a track by search term or direct URL.</p>
  </div>

  <div class="search-bar">
    <div class="search-wrapper">
      <input
        type="text"
        class="search-input"
        placeholder="Search or paste a URL..."
        autocomplete="off"
        bind:value={query}
        on:input={onInput}
        on:keydown={onKeydown}
      />
      {#if open}
        <div class="search-suggestions">
          {#if loading}
            <div class="search-loading">Searching...</div>
          {:else if suggestions.length === 0}
            <div class="search-loading">No results found.</div>
          {:else}
            {#each suggestions as r, i (r.url || i)}
              <button
                type="button"
                class="search-suggestion"
                on:click={() => play(r.url || r.title)}
              >
                <div class="info">
                  <div class="title">{r.title}</div>
                  <div class="channel">{r.channel}</div>
                </div>
                <span class="dur">{fmtTime(r.duration)}</span>
                <span class="source source-{r.source}">{r.source[0].toUpperCase()}</span>
              </button>
            {/each}
          {/if}
        </div>
      {/if}
    </div>
    <button class="search-btn" on:click={() => play(query.trim())}>Queue</button>
  </div>
</section>

<style>
  .search-shell {
    display: grid;
    gap: 10px;
    padding: 16px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--surface);
  }

  .search-head {
    display: grid;
    gap: 4px;
  }

  .search-kicker {
    color: var(--text-muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .search-head p {
    color: var(--text-muted);
    font-size: 13px;
  }

  .search-bar {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 10px;
    align-items: start;
  }

  .search-wrapper {
    position: relative;
    min-width: 0;
  }

  .search-input {
    width: 100%;
    min-height: 42px;
    padding: 0 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-elevated);
    color: var(--text);
  }

  .search-input:focus {
    outline: none;
    border-color: rgba(47, 215, 255, 0.42);
  }

  .search-input::placeholder {
    color: var(--text-muted);
  }

  .search-btn {
    min-width: 84px;
    min-height: 42px;
    padding: 0 14px;
    border: 1px solid var(--primary);
    border-radius: 8px;
    background: var(--primary);
    color: #041018;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
  }

  .search-btn:hover {
    background: var(--primary-hover);
    border-color: var(--primary-hover);
  }

  .search-suggestions {
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    right: 0;
    z-index: 50;
    max-height: 320px;
    overflow-y: auto;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-elevated);
  }

  .search-suggestion {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto auto;
    gap: 10px;
    align-items: center;
    width: 100%;
    padding: 10px 12px;
    border: 0;
    background: transparent;
    color: inherit;
    text-align: left;
    cursor: pointer;
  }

  .search-suggestion:hover {
    background: rgba(255, 255, 255, 0.03);
  }

  .info {
    min-width: 0;
  }

  .title,
  .channel {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .title {
    font-size: 13px;
  }

  .channel,
  .dur {
    color: var(--text-muted);
    font-size: 11px;
  }

  .dur {
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  .source {
    width: 20px;
    height: 20px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    color: #fff;
    font-size: 10px;
    font-weight: 700;
  }

  .source-youtube {
    background: #ff0000;
  }

  .source-spotify {
    background: #1db954;
  }

  .source-soundcloud {
    background: #ff5500;
  }

  .search-loading {
    padding: 14px;
    color: var(--text-muted);
    font-size: 12px;
    text-align: center;
  }

  @media (max-width: 640px) {
    .search-bar {
      grid-template-columns: 1fr;
    }

    .search-btn {
      width: 100%;
    }
  }
</style>
