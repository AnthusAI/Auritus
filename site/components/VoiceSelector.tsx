"use client";

export interface VoiceOption {
  id: string;
  name: string;
  gender?: "Female" | "Male" | "Neutral";
  accent?: string;
  isDefault?: boolean;
}

interface VoiceSelectorProps {
  voices: readonly VoiceOption[];
  selectedVoiceId: string;
  onVoiceChange: (voiceId: string) => void;
  label?: string;
}

/**
 * Accessible, responsive voice selector component for TTS models.
 * Allows users to preview and switch between available preset voices.
 */
export function VoiceSelector({
  voices,
  selectedVoiceId,
  onVoiceChange,
  label = "Voice",
}: VoiceSelectorProps) {
  if (voices.length <= 1) {
    return null;
  }

  const activeVoice = voices.find((v) => v.id === selectedVoiceId) || voices[0];

  return (
    <div className="voice-selector-shell" aria-label={label}>
      <div className="voice-selector-header">
        <span className="voice-selector-label">
          <span className="voice-label-text">{label}:</span>
        </span>
        <span className="voice-active-details">
          <strong>{activeVoice.name}</strong> ({activeVoice.id})
          {activeVoice.accent && (
            <span className="voice-tag">{activeVoice.accent}</span>
          )}
          {activeVoice.gender && (
            <span className="voice-tag">{activeVoice.gender}</span>
          )}
        </span>
      </div>

      <div className="voice-pills-row" role="radiogroup" aria-label={label}>
        {voices.map((voice) => {
          const isSelected = voice.id === selectedVoiceId;
          return (
            <button
              key={voice.id}
              type="button"
              role="radio"
              aria-checked={isSelected}
              className={`voice-pill ${isSelected ? "active" : ""}`}
              onClick={() => onVoiceChange(voice.id)}
            >
              <span className="voice-pill-name">{voice.name}</span>
              <span className="voice-pill-id">{voice.id}</span>
              {voice.isDefault && (
                <span className="voice-pill-badge">Default</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
