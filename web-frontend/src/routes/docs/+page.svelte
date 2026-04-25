<script lang="ts">
  import DocsShell from '$lib/components/DocsShell.svelte';
</script>

<DocsShell title="Wavox Overview">
  <p>
    Wavox is a real-time Discord music bot with a browser dashboard for playback control,
    queue visibility, synced lyrics, and guild-level listening data.
  </p>

  <h2>Features</h2>
  <ul>
    <li>YouTube and Spotify intake</li>
    <li>Queue, seek, shuffle, loop, and previous controls</li>
    <li>WebSocket-driven playback state in the dashboard</li>
    <li>Synchronized lyrics for the active track</li>
    <li>User stats and guild overview pages</li>
  </ul>

  <h2>Quick Start</h2>
  <ol>
    <li>Invite the bot to your Discord server.</li>
    <li>Join a voice channel.</li>
    <li>Use <code>!!play &lt;song name or URL&gt;</code> or the slash command equivalent.</li>
    <li>Open the dashboard to monitor the session in real time.</li>
  </ol>

  <h2>Common Commands</h2>
  <table>
    <thead>
      <tr>
        <th>Command</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody>
      <tr><td><code>/play</code></td><td>Play a track from search or URL</td></tr>
      <tr><td><code>/queue</code></td><td>Show the current queue</td></tr>
      <tr><td><code>/skip</code></td><td>Skip the current track or jump in queue</td></tr>
      <tr><td><code>/goto</code></td><td>Seek to a position in the current track</td></tr>
      <tr><td><code>/status</code></td><td>Show personal listening stats</td></tr>
    </tbody>
  </table>
</DocsShell>
