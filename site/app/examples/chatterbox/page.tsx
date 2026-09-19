"use client";

import { useState } from "react";
import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";
import { VoiceSelector, type VoiceOption } from "@/components/VoiceSelector";

const CHATTERBOX_VOICES: readonly VoiceOption[] = [
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

export default function ChatterboxExamplePage() {
  const [selectedVoice, setSelectedVoice] = useState<string>("steve");
  const currentVoice =
    CHATTERBOX_VOICES.find((v) => v.id === selectedVoice) ||
    CHATTERBOX_VOICES[0];

  return (
    <main className="page">
      <ModelCompareNav currentBackend="chatterbox" />
      <VoiceSelector
        voices={CHATTERBOX_VOICES}
        selectedVoiceId={selectedVoice}
        onVoiceChange={setSelectedVoice}
      />
      <AuritusPlayerHost
        name="Don't Settle"
        byline={`Steve Jobs, 2005 — Chatterbox (${currentVoice.name})`}
      />
      <article className="example-article">
        <JobsCommencementExcerpt
          backendLabel={`Chatterbox — ${currentVoice.name} voice (Resemble AI)`}
        />
      </article>
      <AuritusEmbed
        key={selectedVoice}
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Don't Settle"
        byline={`Steve Jobs, 2005 — Chatterbox (${currentVoice.name})`}
        ttsBackend="chatterbox"
        voiceId={selectedVoice}
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
