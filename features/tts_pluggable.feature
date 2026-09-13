Feature: Pluggable TTS backends
  Workers resolve a backend implementation from the job's tts_backend field so
  Higgs and Qwen can coexist behind one interface.

  Scenario: Registry exposes Higgs, Qwen, and Kokoro backends
    When the TTS backend registry is loaded
    Then registered backends include "higgs"
    And registered backends include "qwen"
    And registered backends include "kokoro"

  Scenario: Qwen resolves from tts_backend without loading a model
    Given tts_backend "qwen"
    When the TTS backend is resolved from the registry
    Then the resolved backend name is "qwen"

  @integration
  Scenario: Job requests the Qwen backend
    Given a claimable job with tts_backend "qwen"
    When the worker generates audio for the job
    Then the Qwen backend is used

  Scenario: Job requests the Higgs backend
    Given a claimable job with tts_backend "higgs"
    When the worker generates audio for the job
    Then the Higgs backend is used
