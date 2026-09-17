Feature: Example pages demonstrate distinct speech
  Kokoro, Qwen, and F5 speak the same Steve Jobs commencement address excerpt so listeners can compare
  backends. Spoken copy is at least two paragraphs. Ignore markup is a separate
  fixture. Playwright requires a playable clip of spoken length on each
  example so a tone stub cannot pass.

  Scenario: Basic example requests Kokoro for the commencement excerpt
    Given the basic example page article
    When the generator extracts TTS text from that root
    Then the TTS text includes "getting fired from Apple was the best thing that could have ever happened to me"
    And the TTS text includes "the only way to do great work is to love what you do"
    And the TTS text does not include "This page speaks that excerpt"
    And the example embed requests tts_backend "kokoro"

  Scenario: Themed example requests Kokoro for the same commencement excerpt
    Given the themed example page article
    When the generator extracts TTS text from that root
    Then the TTS text includes "getting fired from Apple was the best thing that could have ever happened to me"
    And the TTS text includes "the only way to do great work is to love what you do"
    And the example embed requests tts_backend "kokoro"

  Scenario: Qwen example speaks the same commencement excerpt
    Given the Qwen example page article
    When the generator extracts TTS text from that root
    Then the TTS text includes "getting fired from Apple was the best thing that could have ever happened to me"
    And the TTS text includes "the only way to do great work is to love what you do"
    And the TTS text does not include "When on board H.M.S."
    And the example embed requests tts_backend "qwen"

  Scenario: F5 example speaks the same commencement excerpt
    Given the F5 example page article
    When the generator extracts TTS text from that root
    Then the TTS text includes "getting fired from Apple was the best thing that could have ever happened to me"
    And the TTS text includes "the only way to do great work is to love what you do"
    And the TTS text does not include "This page speaks that excerpt"
    And the example embed requests tts_backend "f5"

  Scenario: Chatterbox example speaks the same commencement excerpt
    Given the Chatterbox example page article
    When the generator extracts TTS text from that root
    Then the TTS text includes "getting fired from Apple was the best thing that could have ever happened to me"
    And the TTS text includes "the only way to do great work is to love what you do"
    And the TTS text does not include "This page speaks that excerpt"
    And the example embed requests tts_backend "chatterbox"

  Scenario: Fish example speaks the same commencement excerpt
    Given the Fish example page article
    When the generator extracts TTS text from that root
    Then the TTS text includes "getting fired from Apple was the best thing that could have ever happened to me"
    And the TTS text includes "the only way to do great work is to love what you do"
    And the TTS text does not include "This page speaks that excerpt"
    And the example embed requests tts_backend "fish"

  Scenario: Ignore example omits ignored copy from a longer article
    Given the ignore example page article
    When the generator extracts TTS text from that root
    Then the TTS text includes "The only freedom which deserves the name"
    And the TTS text does not include "This paragraph is ignored"

  Scenario: The player sits above the spoken article
    Given the basic example page layout
    Then the player host is above the example article
    And the player host shows a Play control before the embed boots
