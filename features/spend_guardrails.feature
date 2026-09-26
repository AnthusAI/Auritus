Feature: Spend guardrails
  Batch GPU spend is bounded by AWS Budgets, per-site quotas, and an operator
  kill switch that disables the job queue.

  Scenario: Daily site quota rejects excess job creation
    Given a site key with daily quota 100 and usage 100
    When a new job is created for that site key
    Then the API responds with quota exceeded

  Scenario: Budget breach disables the Batch queue
    Given the daily AWS spend budget threshold is exceeded
    When the budget action runs
    Then the Batch job queue state is "DISABLED"

  Scenario: Operator kill switch disables Batch through the Auritus API
    Given an enabled Batch job queue behind the Auritus API
    When the operator runs auritus killswitch disable
    Then the Batch job queue state is "DISABLED"
    And the kill switch did not fall back to direct AWS access

  Scenario: Operator kill switch re-enables Batch through the Auritus API
    Given a disabled Batch job queue behind the Auritus API
    When the operator runs auritus killswitch enable
    Then the Batch job queue state is "ENABLED"
    And the kill switch did not fall back to direct AWS access
