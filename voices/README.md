# Reference Voice Samples

This directory stores local reference audio clips and accompanying transcripts used for zero-shot voice cloning across TTS backends (such as Chatterbox, F5-TTS, Fish-Speech, and Higgs-v3).

## Gitignore Policy

All binary audio files (`*.wav`, `*.mp3`, `*.m4a`, `*.ogg`, `*.flac`, `*.aac`) in this directory and across the repository are strictly ignored by `.gitignore`.

**Do not commit audio media into git.** Only scripts, documentation, and configuration belong in version control.

---

## Standard File Naming Patterns

To ensure consistent lookup across CLI tools, workers, and test scripts, name your reference voice assets using the following patterns:

| Asset Type | File Pattern | Example | Description |
| :--- | :--- | :--- | :--- |
| **Primary Reference Audio** | `<voice_id>.wav` | `steve_jobs.wav` | Clean 5-15s trimmed audio clip for speaker conditioning. |
| **Reference Transcript** | `<voice_id>.txt` | `steve_jobs.txt` | Exact text spoken in `<voice_id>.wav` (required by F5-TTS). |
| **Full / Source Recording** | `<voice_id>_full.<ext>` | `steve_jobs_full.mp3` | Untrimmed raw source audio file (optional). |

### Identifier Guidelines
- Use lowercase alphanumeric characters and underscores only: `^[a-z0-9_]+$`
- Prefix third-party generated samples with the provider name for clarity:
  - `elevenlabs_adam.wav` + `elevenlabs_adam.txt`
  - `elevenlabs_rachel.wav` + `elevenlabs_rachel.txt`
  - `steve_jobs.wav` + `steve_jobs.txt`

---

## Optimal Audio Specifications for Voice Cloning

For optimal zero-shot synthesis quality across modern neural TTS models:

1. **Duration**: 5 to 15 seconds.
   - Shorter than 3 seconds often lacks sufficient acoustic variety.
   - Longer than 20 seconds risks exceeding transformer context windows and degrades attention.
2. **Format**: 16-bit linear PCM WAV (mono).
3. **Sample Rate**:
   - `24000 Hz` for Chatterbox, F5-TTS, and Higgs-v3.
   - `44100 Hz` for Fish-Speech.
4. **Acoustic Environment**:
   - Dry recording with minimal room reverberation.
   - Zero background music, sound effects, or ambient chatter.
   - Single speaker with clear enunciation and natural pacing.

---

## Utility Scripts

To download and extract the Steve Jobs 2005 Stanford Commencement Address excerpt into this directory:

```bash
python3 scripts/download-commencement-audio.py
```

This downloads the full address into `voices/steve_jobs_full.mp3`, extracts the commencement excerpt into `voices/steve_jobs.wav` at 24 kHz mono (if `ffmpeg` is present), and writes the corresponding `voices/steve_jobs.txt` transcript.
