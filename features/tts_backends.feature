Feature: Pluggable TTS backends
  Auritus workers select a TTS backend per job so Higgs and Qwen prove the
  abstraction.

  @integration
  Scenario: Job requests the Qwen backend
    Given a claimable job with tts_backend "qwen"
    When the worker generates audio for the job
    Then the Qwen backend is used

  Scenario: Job requests the Higgs backend
    Given a claimable job with tts_backend "higgs"
    When the worker generates audio for the job
    Then the Higgs backend is used
