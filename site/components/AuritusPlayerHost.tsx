type AuritusPlayerHostProps = {
  name?: string;
  byline?: string;
};

/** First-paint player slot so example pages show chrome before embed.js boots. */
export function AuritusPlayerHost({ name, byline }: AuritusPlayerHostProps) {
  return (
    <div className="auritus-player-host">
      <div className="auritus-player-placeholder">
        {name ? <p className="auritus-placeholder-name">{name}</p> : null}
        {byline ? <p className="auritus-placeholder-byline">{byline}</p> : null}
        <div className="auritus-placeholder-controls">
          <button type="button" disabled aria-label="Play">
            Play
          </button>
          <div className="auritus-placeholder-track" aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}
