Feature: Content hash scope
  The content hash deduplicates TTS jobs. Only normalized text, voice_id, and
  tts_backend participate. Display name and byline are cosmetic.

  Scenario: Whitespace normalization is stable
    Given the TTS text "Hello   world."
    And voice_id "default"
    And tts_backend "higgs"
    When the content hash is computed
    And the TTS text becomes "Hello world."
    When the content hash is computed again
    Then the two content hashes match

  Scenario: Cosmetic metadata does not affect the hash
    Given the TTS text "Article body"
    And voice_id "default"
    And tts_backend "higgs"
    When the content hash is computed
    And the name and byline are changed
    Then the content hash stays the same

  Scenario: Backend change changes the hash
    Given the TTS text "Article body"
    And voice_id "default"
    And tts_backend "higgs"
    When the content hash is computed
    And tts_backend becomes "qwen"
    Then the content hash changes
