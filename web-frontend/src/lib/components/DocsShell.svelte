<script lang="ts">
  import AppHeader from '$lib/components/AppHeader.svelte';

  export let title: string;
  export let kicker = 'Docs';
</script>

<svelte:head>
  <title>{title} - Wavox</title>
</svelte:head>

<div class="shell">
  <AppHeader compact={true} />

  <main class="docs-main">
    <div class="docs-kicker">{kicker}</div>
    <h1>{title}</h1>
    <div class="docs-content">
      <slot />
    </div>
  </main>
</div>
<style>
  .docs-kicker {
    color: var(--primary);
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
  }
  h1 {
    font-size: 2rem;
    line-height: 1.08;
    margin: 0 0 24px;
  }
</style>
