"use client";

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
          <button
            type="button"
            aria-label="Play"
            onClick={(event) => {
              event.currentTarget
                .closest(".auritus-player-host")
                ?.setAttribute("data-auritus-play-intent", "true");
            }}
          >
            <svg
              viewBox="0 0 24 24"
              width="16"
              height="16"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M8 5.14v13.72a1 1 0 0 0 1.5.86l11-6.86a1 1 0 0 0 0-1.72l-11-6.86a1 1 0 0 0-1.5.86z" />
            </svg>
          </button>
          <div className="auritus-placeholder-track" aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}
