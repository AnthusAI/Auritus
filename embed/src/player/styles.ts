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
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.auritus-play:disabled {
  opacity: 0.45;
  cursor: not-allowed;
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
