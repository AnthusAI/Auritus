Feature: Web console operator authentication
  Operators authenticate to the web console using Cognito credentials,
  receiving short-lived tokens to access protected admin monitoring APIs.

  Scenario: Operator logs in with valid email and password
    Given a mock Cognito endpoint for web client
    When the web console submits email "operator@example.com" and password "secret123"
    Then the console receives an access token and id token
    And the operator identity is authenticated

  Scenario: Operator session includes authorization header in admin requests
    Given an authenticated web console session
    When an admin API request is dispatched
    Then the request header contains a Bearer authorization token

  Scenario: Logging out clears session credentials
    Given an authenticated web console session
    When the operator logs out
    Then the session tokens are cleared

  Scenario: Unauthenticated visitor accessing protected route is redirected to login
    Given an unauthenticated visitor
    When the visitor attempts to navigate to "/jobs"
    Then the visitor is redirected to "/login"

  Scenario: Operator initiates Google Workspace SSO login
    Given the operator is on the login page
    When the operator selects sign in with "Google"
    Then the browser initiates OAuth authorization against the Cognito Hosted UI for provider "Google"

  Scenario: Operator initiates AWS IAM Identity Center SSO login
    Given the operator is on the login page
    When the operator selects sign in with "IdentityCenter"
    Then the browser initiates OAuth authorization against the Cognito Hosted UI for provider "IdentityCenter"

  Scenario: Completing OAuth callback exchanges authorization code for operator session
    Given an OAuth authorization code from an upstream identity provider
    When the callback page processes the code
    Then the console receives an access token and id token
    And the operator identity is authenticated
