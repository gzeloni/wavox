<div class="preview-frame" aria-hidden="true">
  <div class="preview-bar">
    <span>Guild: Studio Queue</span>
    <span>Status: Playing</span>
  </div>

  <div class="preview-panel">
    <div class="preview-row">
      <span class="preview-label">Now Playing</span>
      <span class="preview-value">Midnight Broadcast</span>
    </div>
    <div class="preview-row">
      <span class="preview-label">Progress</span>
      <div class="preview-progress">
        <div class="preview-progress-fill"></div>
      </div>
      <span class="preview-meta">01:28 / 03:41</span>
    </div>
    <div class="preview-row">
      <span class="preview-label">Queue</span>
      <span class="preview-meta">3 tracks pending</span>
    </div>
  </div>

  <div class="preview-columns">
    <div class="preview-list">
      <div class="preview-heading">Up Next</div>
      <div class="preview-item"><span>01</span><span>Signal Bloom</span><span>04:02</span></div>
      <div class="preview-item active"><span>02</span><span>Glass Horizon</span><span>03:18</span></div>
      <div class="preview-item"><span>03</span><span>Blue Transit</span><span>05:11</span></div>
    </div>

    <div class="preview-list">
      <div class="preview-heading">Lyrics</div>
      <div class="preview-line">Streetlight pulse in the rear-view haze</div>
      <div class="preview-line active">Hold the line while the waveform breaks</div>
      <div class="preview-line">Every room keeps time with the bass</div>
      <div class="preview-line">Keep the transport steady</div>
    </div>
  </div>
</div>

<style>
  .preview-frame {
    display: grid;
    gap: 10px;
    height: 100%;
    padding: 14px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--surface);
  }

  .preview-bar,
  .preview-row,
  .preview-item {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .preview-bar {
    justify-content: space-between;
    flex-wrap: wrap;
    color: var(--text-muted);
    font-size: 12px;
  }

  .preview-panel,
  .preview-list {
    border: 1px solid rgba(96, 121, 197, 0.14);
    border-radius: 8px;
    background: transparent;
  }

  .preview-panel {
    padding: 10px;
    display: grid;
    gap: 8px;
  }

  .preview-row {
    min-width: 0;
  }

  .preview-label {
    width: 88px;
    flex-shrink: 0;
    color: var(--text-muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .preview-value,
  .preview-meta {
    font-size: 12px;
  }

  .preview-value {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .preview-meta {
    color: var(--text-muted);
    white-space: nowrap;
  }

  .preview-progress {
    flex: 1;
    min-width: 80px;
    height: 6px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    overflow: hidden;
  }

  .preview-progress-fill {
    width: 46%;
    height: 100%;
    background: var(--primary);
  }

  .preview-columns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .preview-list {
    padding: 10px;
  }

  .preview-heading {
    margin-bottom: 10px;
    color: var(--text-muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .preview-item {
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid rgba(96, 121, 197, 0.14);
    font-size: 12px;
    color: var(--text-muted);
  }

  .preview-item:last-child {
    border-bottom: 0;
  }

  .preview-item span:nth-child(2) {
    flex: 1;
    min-width: 0;
    margin: 0 10px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .preview-item.active,
  .preview-line.active {
    color: var(--text);
  }

  .preview-line {
    padding: 8px 0;
    border-bottom: 1px solid rgba(96, 121, 197, 0.14);
    color: var(--text-muted);
    font-size: 13px;
    line-height: 1.5;
  }

  .preview-line:last-child {
    border-bottom: 0;
  }

  @media (max-width: 768px) {
    .preview-columns {
      grid-template-columns: 1fr;
    }

    .preview-row {
      flex-wrap: wrap;
    }
  }
</style>
