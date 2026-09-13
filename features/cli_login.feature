Feature: CLI operator login
  Operators authenticate with Cognito using email and password
  (USER_PASSWORD_AUTH) and receive short-lived JWTs stored in a mode-0600 file
  under the Auritus config directory.

  Scenario: Login stores Cognito tokens locally
    Given a mock Cognito USER_PASSWORD_AUTH endpoint
    When the operator logs in with email and password
    Then Cognito tokens are cached for the CLI

  @integration
  Scenario: Expired access token refreshes before API calls
    Given cached Cognito tokens that are near expiry
    When the CLI refreshes credentials
    Then a new access token is available

  @integration
  Scenario: Live Google OAuth login via browser loopback
    Given a deployed Cognito user pool with Google IdP
    And the operator completes the OAuth loopback flow
    When the operator runs auritus login via Google OAuth
    Then the CLI can call operator APIs with a valid JWT
