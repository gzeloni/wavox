<script lang="ts">
  import DocsShell from '$lib/components/DocsShell.svelte';
</script>

<DocsShell title="Invite Wavox">
  <p>Before adding Wavox to a server, review the Terms of Service and Privacy Policy.</p>

  <h2>Required Permissions</h2>
  <table>
    <thead>
      <tr>
        <th>Permission</th>
        <th>Why Wavox needs it</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>Connect</td><td>Join voice channels</td></tr>
      <tr><td>Speak</td><td>Play audio</td></tr>
      <tr><td>Send Messages</td><td>Reply to commands and post now playing cards</td></tr>
      <tr><td>Embed Links</td><td>Render rich track and stats embeds</td></tr>
      <tr><td>Add Reactions</td><td>Support likes on now playing messages</td></tr>
      <tr><td>Use Application Commands</td><td>Enable slash commands</td></tr>
    </tbody>
  </table>

  <p>
    You need the <strong>Manage Server</strong> permission on the destination server to add the bot.
  </p>

  <p>
    <a
      href="https://discord.com/oauth2/authorize?client_id=1153526210069004408&permissions=2150647872&integration_type=0&scope=bot+applications.commands"
      target="_blank"
      rel="noreferrer"
    >
      Add Wavox to Discord
    </a>
  </p>
</DocsShell>
