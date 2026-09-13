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

  Scenario: Refresh raises RefreshExpiredError on invalid_grant
    Given cached Cognito tokens with a refresh token
    When Cognito rejects the refresh with invalid_grant
    Then refresh_tokens raises RefreshExpiredError

  Scenario: API client retries once after a 401 by refreshing
    Given cached Cognito tokens with a valid refresh token
    When the API client receives a 401 on the first call
    Then it refreshes and retries the call once

  Scenario: Logout revokes the refresh token server-side
    Given cached Cognito tokens
    When the operator runs auritus logout
    Then the refresh token is revoked at Cognito
    And local credentials are cleared

  Scenario: Worker warns the operator before the refresh token expires
    Given cached Cognito tokens whose refresh token expires in 24 hours
    When the worker checks session state
    Then a warning alert is posted to /alerts/session
    And the warning is throttled to once per day

  Scenario: Worker alerts the operator when the refresh token is dead
    Given cached Cognito tokens with a revoked refresh token
    When the worker fails to refresh
    Then an expired alert is posted to /alerts/session
    And the worker exits with code 2

  Scenario: Alert endpoint rejects unknown emails and rate-limits
    Given the alert endpoint and a known Cognito operator
    When an alert is posted for an unknown email
    Then no email is sent and the response is 404
    When a second warning alert is posted within 6 hours
    Then the response is 429 and no second email is sent
