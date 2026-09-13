Feature: Home page demonstrates Auritus
  The marketing home page speaks a short product pitch with Kokoro.

  Scenario: Home page embed speaks the product pitch with Kokoro
    Given the home page spoken article
    When the generator extracts TTS text from that root
    Then the TTS text includes "Press play"
    And the TTS text includes "What you hear is this page reading itself"
    And the example embed requests tts_backend "kokoro"
