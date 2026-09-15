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

[hidden] {
  display: none !important;
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

/* Shown only before the job is done: a one-shot "start once ready" request,
   since there's no file yet for native controls to attach to. Once done,
   this whole block is replaced by the real <audio controls>. min-height
   matches .auritus-audio below so that swap doesn't itself shift the
   page -- both rows claim the same space regardless of which is hidden. */
.auritus-pending {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 40px;
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

.auritus-play svg {
  margin-left: 2px;
}

.auritus-status {
  font-size: 0.8125rem;
  opacity: 0.9;
}

/* Native browser media controls -- deliberately not reinventing scrubbing,
   volume, or playback-rate UI. accent-color is a best-effort theme hook:
   Chromium and Firefox tint the built-in controls with it, Safari ignores
   it (no further reach into UA-shadow internals from here). */
.auritus-audio {
  display: block;
  width: 100%;
  min-height: 40px;
  accent-color: var(--auritus-accent, #2d5f3f);
}

.auritus-error {
  color: var(--auritus-accent, #c00);
  font-size: 0.8125rem;
  margin-top: 8px;
}
`.trim();
