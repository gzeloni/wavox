<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { session } from '$lib/stores/session';

  onMount(() => {
    session.load();
  });
</script>

<slot />
