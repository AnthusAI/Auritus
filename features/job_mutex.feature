Feature: DynamoDB job mutex
  A pending job may be claimed by at most one worker at a time. Stale claims
  expire so another worker can take over.

  Scenario: First claimer wins
    Given a pending job with content hash "abc123"
    When worker "local:a" claims the job
    Then the job status is "claimed"
    And the claim owner is "local:a"

  Scenario: Second claimer loses while claim is fresh
    Given a job claimed by "local:a" with a fresh claim deadline
    When worker "batch:b" claims the job
    Then the claim is rejected

  @integration
  Scenario: Stale claim allows takeover
    Given a job claimed by "local:a" with an expired claim deadline
    When worker "batch:b" claims the job
    Then the job status is "claimed"
    And the claim owner is "batch:b"
