<script lang="ts">
  import type { Guild } from '$lib/types';
  import { guildInitials, guildIconUrl } from '$lib/utils';

  export let guilds: Guild[];
  export let selectedId: string | null = null;
  export let onSelect: (id: string) => void;
  export let label = 'Your Servers';
</script>

<section class="guilds-section">
  <div class="guilds-head">
    <span class="guilds-label">{label}</span>
    {#if selectedId}
      <span class="guilds-meta">1 selected</span>
    {:else if guilds.length > 0}
      <span class="guilds-meta">{guilds.length} available</span>
    {/if}
  </div>

  {#if guilds.length === 0}
    <div class="empty-inline">No servers available.</div>
  {:else}
    <div class="guild-grid">
      {#each guilds as g (g.id)}
        {@const iconUrl = guildIconUrl(g.id, g.icon)}
        <button
          type="button"
          class="guild-card"
          class:active={selectedId === g.id}
          on:click={() => onSelect(g.id)}
        >
          <div class="guild-icon">
            {#if iconUrl}
              <img src={iconUrl} alt="" />
            {:else}
              {guildInitials(g.name)}
            {/if}
          </div>
          <span class="guild-name">{g.name}</span>
        </button>
      {/each}
    </div>
  {/if}
</section>

<style>
  .guilds-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
  }

  .guild-card {
    font: inherit;
    color: inherit;
  }

  .guilds-meta,
  .empty-inline {
    color: var(--text-muted);
    font-size: 13px;
  }

  .empty-inline {
    padding: 8px 0;
  }
</style>
