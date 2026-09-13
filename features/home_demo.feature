Feature: The home page demonstrates narration on itself
  A visitor can hear what Auritus does instead of only reading about it.
  Playwright requires the ready Kokoro clip to last at least twenty seconds
  so a tone stub cannot pass as the demo.

  Scenario: A visitor hears what Auritus does
    Given the home page spoken article
    When the generator extracts TTS text from that root
    Then the TTS text includes "Press play"
    And the TTS text includes "What you hear is this page reading itself"
    And the TTS text does not include "Narrated by Auritus with Kokoro"
    And the example embed requests tts_backend "kokoro"

  Scenario: The home demo player sits above the spoken article
    Given the home page demo layout
    Then the player host is above the demo article
    And the player host shows a Play control before the embed boots
