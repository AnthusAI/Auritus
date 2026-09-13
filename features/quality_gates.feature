Feature: Quality gates run the product specifications
  CI on develop must fail if Gherkin or Playwright acceptance is red.

  Scenario: CI runs Behave
    Given the CI workflow file
    Then a step runs behave on the features directory

  Scenario: CI runs Playwright acceptance
    Given the CI workflow file
    Then a step runs Playwright against the site
