Feature: Content extraction for TTS
  The generator must speak page content, not chrome or framework payloads.

  Scenario: Script and style payloads are not narrated
    Given a page root with visible text "Hello world"
    And the root also contains a script element with "self.__next_f.push"
    When the generator extracts TTS text from that root
    Then the TTS text includes "Hello world"
    And the TTS text does not include "self.__next_f"

  Scenario: Example pages scope narration to the article
    Given an example page with nav text "Examples" and article text "Basic narration example"
    And the embed root selector is ".example-article"
    When the generator extracts TTS text from that root
    Then the TTS text includes "Basic narration example"
    And the TTS text does not include "Examples"

  Scenario: Ignored paragraphs are not narrated
    Given an article with spoken text "Spoken body text stays in the narration."
    And the article also contains ignored text "This paragraph is ignored."
    When the generator extracts TTS text from that article
    Then the TTS text includes "Spoken body text stays in the narration."
    And the TTS text does not include "This paragraph is ignored."
