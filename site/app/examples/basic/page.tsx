"use client";

import { useState } from "react";
import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";
import { VoiceSelector, type VoiceOption } from "@/components/VoiceSelector";

const KOKORO_VOICES: readonly VoiceOption[] = [
  {
    id: "af_heart",
    name: "Heart",
    gender: "Female",
    accent: "US",
    isDefault: true,
  },
  {
    id: "af_bella",
    name: "Bella",
    gender: "Female",
    accent: "US",
  },
  {
    id: "am_adam",
    name: "Adam",
    gender: "Male",
    accent: "US",
  },
  {
    id: "bf_emma",
    name: "Emma",
    gender: "Female",
    accent: "UK",
  },
];

export default function BasicExamplePage() {
  const [selectedVoice, setSelectedVoice] = useState<string>("af_heart");
  const currentVoice =
    KOKORO_VOICES.find((v) => v.id === selectedVoice) || KOKORO_VOICES[0];

  return (
    <main className="page">
      <ModelCompareNav currentBackend="kokoro" />
      <VoiceSelector
        voices={KOKORO_VOICES}
        selectedVoiceId={selectedVoice}
        onVoiceChange={setSelectedVoice}
      />
      <AuritusPlayerHost
        name="Don't Settle"
        byline={`Steve Jobs, 2005 — Kokoro (${currentVoice.name})`}
      />
      <article className="example-article">
        <JobsCommencementExcerpt backendLabel={`Kokoro (${currentVoice.id})`} />
      </article>
      <AuritusEmbed
        key={selectedVoice}
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Don't Settle"
        byline={`Steve Jobs, 2005 — Kokoro (${currentVoice.name})`}
        ttsBackend="kokoro"
        voiceId={selectedVoice}
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
