Feature: Interactive getting started onboarding guide
  Developers and operators follow an interactive, animated getting-started
  guide that visually breaks down deployment, presents side-by-side identity
  and TTS model decision cards with expanding details and audio previews, and
  dynamically configures their embed code snippet.

  Scenario: Guide displays three side-by-side authentication choices
    Given a visitor on the getting started documentation page
    When the visitor views the authentication decision section
    Then three options are displayed side-by-side: "Native Cognito", "Google Workspace", and "AWS IAM Identity Center"
    And each option presents a brief recommendation and link to deep-dive documentation

  Scenario: Selecting an authentication option expands its step-by-step instructions
    Given a visitor on the getting started documentation page
    When the visitor selects the "Google Workspace" authentication option
    Then the option card expands to reveal step-by-step setup instructions
    And the corresponding CLI login command "auritus login --sso google" is displayed

  Scenario: Model selection section updates the embed code
    Given a visitor on the getting started documentation page
    When the visitor reviews the voice model options
    When the visitor selects the "Qwen3-TTS" model option
    Then the interactive embed code snippet updates to backend "qwen" and voice "Ryan"

  Scenario: Model cards state the license that governs each model's weights
    Given a visitor on the getting started documentation page
    When the visitor reviews the voice model options
    Then the "Higgs Audio v3" card shows the license "Non-commercial research"
    And the "Qwen3-TTS" card shows the license "Apache 2.0"
    And the "Kokoro-82M" card shows the license "Apache 2.0"
    And no model card is named "Higgs-v2"

  Scenario: Model cards state only sourced sizes and no unmeasured latency
    Given a visitor on the getting started documentation page
    When the visitor reviews the voice model options
    Then the "Qwen3-TTS" card shows the size "1.7B params"
    And the "Higgs Audio v3" card shows the size "4B params"
    And no model card shows a latency figure

  Scenario: Model cards never depend on expiring job redeem links
    Given a visitor on the getting started documentation page
    When the visitor reviews the voice model options
    Then no model card references an API job redeem URL
