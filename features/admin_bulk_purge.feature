Feature: Bulk job cleanup

  Scenario: Operator previews a bulk delete before running it
    Given twelve jobs exist for site "site-a"
    When the operator previews a bulk delete for site "site-a"
    Then the response reports twelve matching jobs
    And no jobs are deleted

  Scenario: Operator deletes every failed job
    Given three jobs exist with status "failed"
    And two jobs exist with status "done"
    When the operator bulk deletes jobs with status "failed"
    Then the three failed jobs are removed
    And the two done jobs remain

  Scenario: Operator deletes jobs older than a cutoff
    Given a job created ninety days ago
    And a job created today
    When the operator bulk deletes jobs older than thirty days
    Then only the ninety day old job is removed

  Scenario: Bulk delete removes audio objects
    Given three jobs exist with status "done" and stored audio objects
    When the operator bulk deletes jobs with status "done"
    Then all three audio objects are removed from the audio bucket

  Scenario: Bulk delete requires at least one filter
    When the operator bulk deletes with no filter
    Then the response is a bad request
    And no jobs are deleted
