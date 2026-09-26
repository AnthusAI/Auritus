Feature: Batch render mode
  A host's own cloud deployment (the SpeechRenderer construct) runs the worker
  image in render mode. It reads one request, speaks it with the speech
  library, and writes the audio and its metadata where the host asked. It
  never talks to the Auritus API.

  Scenario: A render request writes speech and its metadata
    Given a render request for "Hello there. [[auritus:break]] Welcome." with voice "fake:plain"
    When the renderer runs
    Then it exits successfully
    And the output has "speech.wav" as mono WAV audio
    And "speech.json" records 2 timed segments, the sample rate, duration, provenance and request key
    And "speech.json" echoes the request

  Scenario: A render that cannot run writes an error and fails
    Given a render request for "Hello" with voice "chatterbox:default"
    And the speech model libraries are not installed
    When the renderer runs
    Then it exits with a failure
    And "error.json" says "BackendUnavailable" and names the missing module
    And the output has no "speech.wav"

  Scenario: A backend outside the deployment's allowed list is refused
    Given the deployment allows only the "kokoro" backend
    And a render request for "Hello" with voice "fake:plain"
    When the renderer runs
    Then it exits with a failure
    And "error.json" says "BackendNotAllowed"

  Scenario: A malformed request is refused before any synthesis
    Given a render request with no text
    When the renderer runs
    Then it exits with a failure
    And "error.json" says "InvalidRequest"
