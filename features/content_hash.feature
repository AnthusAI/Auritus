Feature: Content hash scope
  The content hash deduplicates TTS jobs. Only normalized text, voice_id, and
  tts_backend participate. Display name and byline are cosmetic.

  Scenario: Whitespace normalization is stable
    Given the TTS text "Hello   world."
    And voice_id "af_heart"
    And tts_backend "higgs"
    When the content hash is computed
    And the TTS text becomes "Hello world."
    When the content hash is computed again
    Then the two content hashes match

  Scenario: Cosmetic metadata does not affect the hash
    Given the TTS text "Article body"
    And voice_id "af_heart"
    And tts_backend "higgs"
    When the content hash is computed
    And the name and byline are changed
    Then the content hash stays the same

  Scenario: Backend change changes the hash
    Given the TTS text "Article body"
    And voice_id "af_heart"
    And tts_backend "kokoro"
    When the content hash is computed
    And tts_backend becomes "qwen"
    Then the content hash changes

  Scenario Outline: The API computes the canonical content hash
    The content hash is the SHA-256 of the normalized text, the voice_id, and
    the tts_backend joined by NUL characters. Normalization applies Unicode
    NFC, collapses every run of whitespace (including non-breaking and other
    Unicode spaces) to one space, and trims. The embed computes the same
    hash in the browser, so these vectors are shared with its tests.

    Given a registered site key
    When a job is created for <text fixture> with voice "af_heart" on "kokoro"
    Then the job is created with content hash "<content hash>"
    And the stored job text is "<normalized text>"

    Examples:
      | text fixture                                   | normalized text        | content hash                                                     |
      | the text "Hello   world.\nNew line."           | Hello world. New line. | be5ee98501f1984fe1eb93a0ab8e96b3d0f87da538eb37bfb92a702214b0cb6f |
      | a decomposed accent between Unicode spaces     | Café bar               | 6f4ec549d0c26edd736a90e4132de08342f7ededbf34fdef79cd416d011e2824 |

  Scenario: The API rejects a content hash that does not match the text
    A caller holding only a public site key must not be able to bind its own
    text to another page's content hash.

    Given a registered site key
    When a job is created for the text "Attacker narration" claiming the content hash of "Hello world. New line."
    Then the API rejects the job with "content_hash_mismatch"
    And no job exists for the content hash of "Hello world. New line."

  Scenario: Job creation does not reveal the job's worker token
    Given a registered site key
    When a job is created for the text "Article body" with voice "af_heart" on "kokoro"
    Then the job creation response carries no job token
    And a caller with only the site key cannot claim that job
