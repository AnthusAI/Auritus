"use client";

import { useState } from "react";
import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";
import { VoiceSelector, type VoiceOption } from "@/components/VoiceSelector";

const QWEN_VOICES: readonly VoiceOption[] = [
  {
    id: "Ryan",
    name: "Ryan",
    gender: "Male",
    accent: "Dynamic",
    isDefault: true,
  },
  {
    id: "Vivian",
    name: "Vivian",
    gender: "Female",
    accent: "Bright",
  },
  {
    id: "Aiden",
    name: "Aiden",
    gender: "Male",
    accent: "Warm",
  },
  {
    id: "Sohee",
    name: "Sohee",
    gender: "Female",
    accent: "Soft",
  },
];

export default function QwenExamplePage() {
  const [selectedVoice, setSelectedVoice] = useState<string>("Ryan");
  const currentVoice =
    QWEN_VOICES.find((v) => v.id === selectedVoice) || QWEN_VOICES[0];

  return (
    <main className="page">
      <ModelCompareNav currentBackend="qwen" />
      <VoiceSelector
        voices={QWEN_VOICES}
        selectedVoiceId={selectedVoice}
        onVoiceChange={setSelectedVoice}
      />
      <AuritusPlayerHost
        name="Don't Settle"
        byline={`Steve Jobs, 2005 — Qwen (${currentVoice.name})`}
      />
      <article className="example-article">
        <JobsCommencementExcerpt backendLabel={`Qwen (${currentVoice.id})`} />
      </article>
      <AuritusEmbed
        key={selectedVoice}
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Don't Settle"
        byline={`Steve Jobs, 2005 — Qwen (${currentVoice.name})`}
        ttsBackend="qwen"
        voiceId={selectedVoice}
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
