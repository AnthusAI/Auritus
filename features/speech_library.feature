Feature: Auritus as an embeddable speech library
  Host applications (Apricity is the first) call Auritus offline through a
  typed API: text and a voice in, speech audio plus its timing and
  provenance out, with a stable key for caching the result.

  Scenario: Synthesize speech with a typed request
    When I synthesize "Hello there. [[auritus:break]] Welcome." with voice "fake:plain"
    Then I receive mono WAV audio at 24000 Hz
    And the reported duration matches the audio
    And the result lists 2 timed segments
    And segment 1 is "Hello there." and ends before segment 2 "Welcome." starts
    And the provenance records engine "auritus", backend "fake", model "fake-tone" and voice "fake:plain"

  Scenario: A voice spec without an id uses the backend's default voice
    When I parse the voice spec "kokoro"
    Then the voice backend is "kokoro" and its id is "default"

  Scenario: Speed changes the audio and the request key
    When I synthesize "Steady pace." with voice "fake:plain" at speed 2.0
    Then the audio is shorter than the same line at speed 1.0

  Scenario: A backend that cannot change speed refuses to pretend
    When I synthesize "Hello" with voice "qwen:Ryan" at speed 1.5
    Then synthesis fails because "qwen" does not support speed

  Scenario: The request key is stable and sensitive to every input
    Given the request "Hello" with voice "fake:plain"
    Then its request key is the same when computed twice
    And its request key changes when the text is "Hello!"
    And its request key changes when the voice is "fake:other"
    And its request key changes when the speed is 1.25
    And its request key changes when the seed is 7
    And the synthesized result carries the same request key
