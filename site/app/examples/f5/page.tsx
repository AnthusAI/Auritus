"use client";

import { useState } from "react";
import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";
import { VoiceSelector, type VoiceOption } from "@/components/VoiceSelector";

const F5_VOICES: readonly VoiceOption[] = [
  {
    id: "steve",
    name: "Steve",
    gender: "Male",
    accent: "US",
    isDefault: true,
  },
  {
    id: "serious",
    name: "Serious",
    gender: "Male",
    accent: "US",
  },
];

export default function F5ExamplePage() {
  const [selectedVoice, setSelectedVoice] = useState<string>("steve");
  const currentVoice =
    F5_VOICES.find((v) => v.id === selectedVoice) || F5_VOICES[0];

  return (
    <main className="page">
      <ModelCompareNav currentBackend="f5" />
      <VoiceSelector
        voices={F5_VOICES}
        selectedVoiceId={selectedVoice}
        onVoiceChange={setSelectedVoice}
      />
      <AuritusPlayerHost
        name="Don't Settle"
        byline={`Steve Jobs, 2005 — F5-TTS (${currentVoice.name})`}
      />
      <article className="example-article">
        <JobsCommencementExcerpt
          backendLabel={`F5-TTS — ${currentVoice.name} voice (Flow-matching)`}
        />
      </article>
      <AuritusEmbed
        key={selectedVoice}
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Don't Settle"
        byline={`Steve Jobs, 2005 — F5-TTS (${currentVoice.name})`}
        ttsBackend="f5"
        voiceId={selectedVoice}
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
