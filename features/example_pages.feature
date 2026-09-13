Feature: Example pages demonstrate distinct speech
  Each aurit.us example has its own article text and a chosen TTS backend so
  pages do not share audio. Spoken copy is at least two paragraphs.

  Scenario: Basic example requests Kokoro for the Gettysburg excerpt
    Given the basic example page article
    When the generator extracts TTS text from that root
    Then the TTS text includes "Four score and seven years ago"
    And the TTS text includes "Now we are engaged in a great civil war"
    And the example embed requests tts_backend "kokoro"

  Scenario: Themed example requests Kokoro for the Austen excerpt
    Given the themed example page article
    When the generator extracts TTS text from that root
    Then the TTS text includes "It is a truth universally acknowledged"
    And the TTS text includes "However little known the feelings"
    And the example embed requests tts_backend "kokoro"

  Scenario: Qwen example requests the Qwen backend
    Given the Qwen example page article
    When the generator extracts TTS text from that root
    Then the TTS text includes "When on board H.M.S."
    And the example embed requests tts_backend "qwen"

  Scenario: Ignore example omits ignored copy from a longer article
    Given the ignore example page article
    When the generator extracts TTS text from that root
    Then the TTS text includes "The only freedom which deserves the name"
    And the TTS text does not include "This paragraph is ignored"

  Scenario: The player sits above the spoken article
    Given the basic example page layout
    Then the player host is above the example article
    And the player host shows "Loading player" before the embed boots

