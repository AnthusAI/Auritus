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

  Scenario: Model selection section presents audio previews and updates embed code
    Given a visitor on the getting started documentation page
    When the visitor reviews the voice model options
    Then each model option includes an inline audio preview
    When the visitor selects the "Qwen3-TTS" model option
    Then the interactive embed code snippet updates to backend "qwen" and voice "Ryan"
