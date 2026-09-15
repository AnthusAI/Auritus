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

  Scenario: Kokoro uses af_heart when voice_id is omitted
    Given a Kokoro job without an explicit voice_id
    When the Kokoro voice is resolved for synthesis
    Then the Kokoro voice_id is "af_heart"

  Scenario: Kokoro maps legacy default voice_id to af_heart
    Given a Kokoro job with voice_id "default"
    When the Kokoro voice is resolved for synthesis
    Then the Kokoro voice_id is "af_heart"

  Scenario: Qwen uses Ryan when voice_id is omitted
    Given a Qwen job without an explicit voice_id
    When the Qwen voice is resolved for synthesis
    Then the Qwen voice_id is "Ryan"

  Scenario: Qwen maps legacy Chelsie voice_id to Ryan
    Given a Qwen job with voice_id "Chelsie"
    When the Qwen voice is resolved for synthesis
    Then the Qwen voice_id is "Ryan"

  Scenario: F5 uses default when voice_id is omitted
    Given an F5 job without an explicit voice_id
    When the F5 voice is resolved for synthesis
    Then the F5 voice_id is "default"

  Scenario: F5 maps empty voice_id to default
    Given an F5 job with voice_id ""
    When the F5 voice is resolved for synthesis
    Then the F5 voice_id is "default"

  Scenario: Higgs uses default when voice_id is omitted
    Given a Higgs job without an explicit voice_id
    When the Higgs voice is resolved for synthesis
    Then the Higgs voice_id is "default"

  Scenario: Higgs maps empty voice_id to default
    Given a Higgs job with voice_id ""
    When the Higgs voice is resolved for synthesis
    Then the Higgs voice_id is "default"

  Scenario: Chatterbox uses default when voice_id is omitted
    Given a Chatterbox job without an explicit voice_id
    When the Chatterbox voice is resolved for synthesis
    Then the Chatterbox voice_id is "default"

  Scenario: Chatterbox maps empty voice_id to default
    Given a Chatterbox job with voice_id ""
    When the Chatterbox voice is resolved for synthesis
    Then the Chatterbox voice_id is "default"

