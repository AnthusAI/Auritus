Feature: Recovering failed and stuck jobs

  Scenario: Operator retries a failed job
    Given a failed job for retry
    When the operator retries that content hash
    Then the retried job status is "pending"
    And the retried job has no error message

  Scenario: Operator releases a claim held by a crashed worker
    Given a claimed job for retry with an expired claim deadline
    When the operator retries that content hash
    Then the retried job status is "pending"
    And the retried job has no claim owner

  Scenario: Releasing a claim that is still live is rejected
    Given a claimed job for retry with a live claim deadline
    When the operator retries that content hash
    Then the response is a conflict
    And the retried job is still claimed

  Scenario: Operator force-releases a live claim
    Given a claimed job for retry with a live claim deadline
    When the operator force-retries that content hash
    Then the retried job status is "pending"

  Scenario: Retrying a pending job is rejected
    Given a pending job for retry
    When the operator retries that content hash
    Then the response is a conflict
