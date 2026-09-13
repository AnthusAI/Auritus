Feature: Admin monitoring and queue control API
  Operators require protected endpoints to view aggregate job KPIs, query
  jobs with status filters, inspect single job details, and toggle the Batch
  GPU queue state.

  Scenario: Operator queries admin overview KPIs
    Given a set of historical jobs with varied statuses and worker types
    When the operator requests the admin overview
    Then the response contains job status counts
    And the response contains worker breakdown counts
    And the response contains average duration seconds

  Scenario: Operator filters jobs by status
    Given a set of historical jobs with varied statuses and worker types
    When the operator lists jobs with status "done"
    Then all returned jobs have status "done"

  Scenario: Operator inspects single job details
    Given a completed job with content hash "inspect-hash-123"
    When the operator requests job details for "inspect-hash-123"
    Then the response includes the audio URL
    And the response includes worker attribution and timestamps

  Scenario: Operator toggles the AWS Batch queue state
    Given an enabled Batch job queue
    When the operator toggles the queue state to "DISABLED"
    Then the Batch job queue state is "DISABLED"
