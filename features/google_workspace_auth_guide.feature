Feature: Google Workspace SSO Setup and Configuration Guide
  Operators and administrators need clear, detailed, step-by-step documentation
  for integrating Google Workspace with AWS Cognito and Auritus, including
  explicit authorized redirect URIs, authorized JavaScript origins, AWS Secrets
  Manager configuration, and troubleshooting common OAuth errors.

  Scenario: Google Workspace documentation provides exact OAuth URI endpoints
    Given an administrator configuring Google Workspace SSO for Auritus
    When the administrator views the Google Workspace setup documentation
    Then the documentation specifies the authorized redirect URI format "https://<cognito-domain-prefix>.auth.<region>.amazoncognito.com/oauth2/idpresponse"
    And the documentation specifies the authorized JavaScript origins for Cognito and local developer consoles
    And the documentation includes instructions for AWS Secrets Manager credentials structure
    And the documentation provides troubleshooting steps for "redirect_uri_mismatch"

  Scenario: Getting started wizard links directly to Google Workspace documentation
    Given a visitor on the getting started documentation page
    When the visitor selects the "Google Workspace" authentication option
    Then the deep-dive documentation link navigates to "/docs/security/google-workspace"
    And the inline expanding drawer details the authorized redirect URI and javascript origins
