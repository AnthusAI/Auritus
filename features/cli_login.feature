Feature: CLI operator login
  Operators authenticate with Cognito using email and password
  (USER_PASSWORD_AUTH) and receive short-lived JWTs stored in a mode-0600 file
  under the Auritus config directory.

  Scenario: Login stores Cognito tokens locally
    Given a mock Cognito USER_PASSWORD_AUTH endpoint
    When the operator logs in with email and password
    Then Cognito tokens are cached for the CLI

  Scenario: Expired access token refreshes before API calls
    Given cached Cognito tokens that are near expiry
    When the CLI refreshes credentials
    Then a new access token is available
