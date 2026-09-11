Feature: Job claim mutex
  Only one worker may claim a pending job through the conditional DynamoDB put.

  Scenario: First claimer wins
    Given a pending job with content hash "abc123"
    When worker "local:a" claims the job
    Then the job status is "claimed"
    And the claim owner is "local:a"

  Scenario: Second claimer loses
    Given a job claimed by "local:a" with a fresh claim deadline
    When worker "batch:b" claims the job
    Then the claim is rejected
