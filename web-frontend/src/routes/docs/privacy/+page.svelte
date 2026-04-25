<script lang="ts">
  import DocsShell from '$lib/components/DocsShell.svelte';
</script>

<DocsShell title="Privacy Policy">
  <p><em>Last updated: March 18, 2026</em></p>

  <h2>Information We Collect</h2>
  <ul>
    <li>Discord user IDs</li>
    <li>Song playback data such as titles and timestamps</li>
    <li>Server identifiers required for queue and playback scoping</li>
  </ul>

  <h2>How Data Is Used</h2>
  <ul>
    <li>Provide playback and queue management features</li>
    <li>Generate listening history and usage statistics</li>
    <li>Operate the dashboard and real-time playback state</li>
  </ul>

  <h2>Storage</h2>
  <p>
    Listening data is stored locally in SQLite. Session and runtime state are handled by the
    application server and Redis.
  </p>

  <h2>Third-Party Services</h2>
  <ul>
    <li><a href="https://discord.com/privacy" target="_blank" rel="noreferrer">Discord</a></li>
    <li><a href="https://www.youtube.com/t/terms" target="_blank" rel="noreferrer">YouTube</a></li>
    <li><a href="https://www.spotify.com/legal/privacy-policy/" target="_blank" rel="noreferrer">Spotify</a></li>
  </ul>

  <h2>Contact</h2>
  <p>For privacy questions or deletion requests, contact the project maintainer through GitHub.</p>
</DocsShell>
