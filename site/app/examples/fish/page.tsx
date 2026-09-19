"use client";

import { useState } from "react";
import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";
import { VoiceSelector, type VoiceOption } from "@/components/VoiceSelector";

const FISH_VOICES: readonly VoiceOption[] = [
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

export default function FishExamplePage() {
  const [selectedVoice, setSelectedVoice] = useState<string>("steve");
  const currentVoice =
    FISH_VOICES.find((v) => v.id === selectedVoice) || FISH_VOICES[0];

  return (
    <main className="page">
      <ModelCompareNav currentBackend="fish" />
      <VoiceSelector
        voices={FISH_VOICES}
        selectedVoiceId={selectedVoice}
        onVoiceChange={setSelectedVoice}
      />
      <AuritusPlayerHost
        name="Don't Settle"
        byline={`Steve Jobs, 2005 — Fish Speech (${currentVoice.name})`}
      />
      <article className="example-article">
        <JobsCommencementExcerpt
          backendLabel={`Fish Speech — ${currentVoice.name} voice (Fish Audio)`}
        />
      </article>
      <AuritusEmbed
        key={selectedVoice}
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Don't Settle"
        byline={`Steve Jobs, 2005 — Fish Speech (${currentVoice.name})`}
        ttsBackend="fish"
        voiceId={selectedVoice}
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
