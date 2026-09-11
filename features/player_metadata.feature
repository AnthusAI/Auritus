Feature: Player display metadata
  The player shows a title and byline from embed attributes, with document
  fallbacks. Metadata is display-only and does not affect the content hash.

  Scenario: Script attributes supply title and byline
    Given an embed script with data-auritus-name "My article"
    And data-auritus-byline "By Example Author"
    When player metadata is read from the script
    Then the player title is "My article"
    And the player byline is "By Example Author"

  Scenario: Missing attributes fall back to document title and hostname
    Given an embed script without name or byline attributes
    And document title "Page title"
    And page hostname "news.example.com"
    When player metadata is read from the script
    Then the player title is "Page title"
    And the player byline is "news.example.com"
