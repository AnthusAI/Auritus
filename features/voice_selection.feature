Feature: Voice selection and fine-grained voice markup
  Auritus supports selecting a specific voice via the embed tag and fine-grained
  per-element voice markup in content, with interactive voice selectors on example pages.

  Scenario: Embed tag configures a specific voice
    Given an embed tag with tts_backend "kokoro" and data-auritus-voice "am_adam"
    When the embed configuration is parsed
    Then the resolved voice_id is "am_adam"

  Scenario: Embed tag omits voice for Qwen backend
    Given an embed tag with tts_backend "qwen" and no data-auritus-voice attribute
    When the embed configuration is parsed
    Then the resolved voice_id is "Ryan"

  Scenario: Embed tag omits voice for Kokoro backend
    Given an embed tag with tts_backend "kokoro" and no data-auritus-voice attribute
    When the embed configuration is parsed
    Then the resolved voice_id is "af_heart"

  Scenario: Content with fine-grained voice markup extracts voiced blocks
    Given an article containing standard text and an element with data-auritus-voice "af_bella"
    When the generator extracts TTS text from that root
    Then the TTS text contains voice marker "[[auritus:voice:af_bella]]"
    And the TTS text contains voice reset marker "[[auritus:voice:reset]]"

  Scenario: Voiced segments are parsed for multi-speaker synthesis
    Given TTS text containing standard speech and a marked voice segment "[[auritus:voice:am_adam]] Lincoln speech [[auritus:voice:reset]]"
    When the backend parses voiced segments with default voice "af_heart"
    Then the parsed segments contain text "Lincoln speech" with voice "am_adam"

  Scenario: Content hash differs between voices for identical text
    Given article text "Four score and seven years ago"
    When content hashes are computed for backend "kokoro" with voice "af_heart" and voice "am_adam"
    Then the content hashes are distinct

  Scenario: Content hash differs when fine-grained voice markup is present
    Given plain article text "Four score and seven years ago"
    And voiced article text "[[auritus:voice:am_adam]] Four score and seven years ago [[auritus:voice:reset]]"
    When content hashes are computed for both texts with backend "kokoro" and default voice "af_heart"
    Then the content hashes are distinct
