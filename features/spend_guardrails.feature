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

  Scenario: A pending job the Batch fallback cannot run is marked failed
    The fallback submits a job that no local worker claimed within the race
    window. If AWS Batch refuses the submission (for example because the
    spend guardrails or the kill switch disabled the queue) or fails the job
    before a worker claims it, the job is marked failed instead of staying
    pending forever. While the kill switch is engaged, unclaimed jobs
    therefore fail after the race window and need an operator retry.

    Given the deployed Batch fallback state machine
    When the fallback's Batch job for a pending job fails or is refused
    Then the fallback marks the job failed with error "batch_fallback_failed"
    And the fallback only marks the job failed while it is still pending
    And the fallback execution ends as failed
