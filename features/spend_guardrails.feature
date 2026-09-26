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

  Scenario: Operator kill switch disables Batch
    Given an enabled Batch job queue
    When the operator runs auritus killswitch disable
    Then the Batch job queue state is "DISABLED"

  Scenario: A job whose Batch submission is refused is marked failed
    Given the deployed Batch fallback state machine
    When the fallback's Batch submission for a pending job is refused
    Then the fallback marks the job failed with error "batch_submit_failed"
    And the fallback only marks the job failed while it is still pending
    And the fallback execution ends as failed
