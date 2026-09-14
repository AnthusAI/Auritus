/** Default shadow-DOM styles driven by --auritus-* CSS variables on the host. */
export const PLAYER_STYLES = `
:host {
  display: block;
  font-family: var(--auritus-font, inherit);
  color: var(--auritus-fg, #14201a);
  background: var(--auritus-bg, #ffffff);
  border: 1px solid var(--auritus-border, rgba(20, 32, 26, 0.14));
  border-radius: var(--auritus-radius, 10px);
  box-shadow: var(--auritus-shadow, 0 8px 24px rgba(20, 32, 26, 0.08));
  box-sizing: border-box;
}

*, *::before, *::after {
  box-sizing: border-box;
}

.auritus-player {
  padding: 12px 14px;
  border-radius: inherit;
}

.auritus-meta {
  margin-bottom: 10px;
}

.auritus-name {
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.3;
  margin: 0;
}

.auritus-byline {
  font-size: 0.875rem;
  opacity: 0.85;
  margin: 4px 0 0;
}

.auritus-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.auritus-play {
  appearance: none;
  border: none;
  cursor: pointer;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--auritus-accent, #2d5f3f);
  color: var(--auritus-play-fg, #ffffff);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

.auritus-play:hover:not(:disabled) {
  opacity: 0.92;
  transform: scale(1.04);
}

.auritus-play:active:not(:disabled) {
  transform: scale(0.96);
}

.auritus-play:focus-visible {
  outline: 2px solid var(--auritus-accent, #2d5f3f);
  outline-offset: 2px;
}

.auritus-play:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.auritus-play .auritus-icon-play {
  margin-left: 2px;
}

.auritus-play .auritus-icon-pause {
  display: none;
}

.auritus-play[data-playing="true"] .auritus-icon-play {
  display: none;
}

.auritus-play[data-playing="true"] .auritus-icon-pause {
  display: block;
}

.auritus-time {
  font-size: 0.75rem;
  font-variant-numeric: tabular-nums;
  opacity: 0.8;
  white-space: nowrap;
  user-select: none;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
}

.auritus-time[hidden] {
  display: none;
}

.auritus-status {
  font-size: 0.8125rem;
  opacity: 0.9;
}

.auritus-track {
  flex: 1;
  height: 4px;
  border-radius: 999px;
  background: var(--auritus-track, color-mix(in srgb, currentColor 25%, transparent));
  overflow: hidden;
}

.auritus-track-fill {
  height: 100%;
  width: 0%;
  background: var(--auritus-accent, currentColor);
  transition: width 0.1s linear;
}

.auritus-error {
  color: var(--auritus-accent, #c00);
  font-size: 0.8125rem;
  margin-top: 8px;
}
`.trim();
