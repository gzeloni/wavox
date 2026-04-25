<script lang="ts">
  import type { Guild } from '$lib/types';
  import { guildInitials, guildIconUrl } from '$lib/utils';

  export let guilds: Guild[];
  export let selectedId: string | null = null;
  export let onSelect: (id: string) => void;
  export let label = 'Your Servers';
</script>

<section class="guilds-section">
  <span class="guilds-label">{label}</span>
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
  .guild-card {
    font: inherit;
    color: inherit;
  }
  .empty-inline {
    color: var(--text-muted);
    font-size: 13px;
    padding: 8px 0;
  }
</style>
