Feature: Retention of generated audio and job records

  Scenario: A completed job is stamped with an expiry when retention is enabled
    Given the retention period is ninety days
    When a job is marked done
    Then the job record carries an expiry ninety days in the future

  Scenario: A completed job carries no expiry when retention is disabled
    Given the retention period is disabled
    When a job is marked done
    Then the job record carries no expiry

  Scenario: Regenerating a job clears its stale expiry until it completes again
    Given the retention period is ninety days
    And a job was marked done sixty days ago with an expiry from that completion
    When the operator forces regeneration of that content hash
    Then the regenerated job carries no expiry
