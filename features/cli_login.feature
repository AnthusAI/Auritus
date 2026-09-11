Feature: CLI operator login
  Operators authenticate with Cognito using Google OAuth and receive short-lived
  JWTs stored in the system keyring (or a mode-0600 file fallback).

  Scenario: Login stores Cognito tokens locally
    Given a mock Cognito token endpoint
    And the operator completes the OAuth loopback flow
    Then Cognito tokens are cached for the CLI

  Scenario: Expired access token refreshes before API calls
    Given cached Cognito tokens that are near expiry
    When the CLI refreshes credentials
    Then a new access token is available

  @integration
  Scenario: Live Google OAuth login
    Given a deployed Cognito user pool with Google IdP
    When the operator runs auritus login
    Then the CLI can call operator APIs with a valid JWT
