Feature: The home page demonstrates narration on itself
  A visitor can hear what Auritus does instead of only reading about it.
  Playwright requires the ready Kokoro clip to last at least twenty seconds
  so a tone stub cannot pass as the demo.

  Scenario: A visitor hears what Auritus does
    Given the home page spoken article
    When the generator extracts TTS text from that root
    Then the TTS text does not include "Press play"
    And the TTS text does not include "What you hear is this page reading itself"
    And the TTS text does not include "Narrated by Auritus with Kokoro"
    And the TTS text includes "Auritus turns any article into audio on demand"
    And the example embed requests tts_backend "kokoro"

  Scenario: The home demo player sits above the spoken article
    Given the home page demo layout
    Then the player host is above the demo article
    And the player host shows a Play control before the embed boots

  Scenario: Primary calls to action have consistent square button profiles
    Given the marketing site styles
    Then the header call to action and hero call to action share a square border radius

  Scenario: The hero section sits close to the header without excessive vertical whitespace
    Given the marketing site styles
    Then the marketing hero does not enforce full viewport centering
    And the marketing hero vertical padding is compact

  Scenario: The What Just Happened flow section has vertical breathing room below the hero section
    Given the marketing site styles
    Then the flow section has top padding separating it from the hero section


