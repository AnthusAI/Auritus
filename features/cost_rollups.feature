Feature: Daily cost rollups

  Scenario: A completed Batch job adds to the daily rollup
    Given the daily rollup for a site is empty
    When a Batch job for that site completes with a gpu cost
    Then the daily rollup gpu cost equals that job cost
    And the daily rollup batch job count is one

  Scenario: A local job adds platform cost but no gpu cost
    Given the daily rollup for a site is empty
    When a local job for that site completes
    Then the daily rollup gpu cost is zero
    And the daily rollup local job count is one

  Scenario: Rollups separate sites
    Given jobs complete for site "site-a" and site "site-b"
    Then each site has its own daily rollup

  Scenario: A retried rollup write does not double count
    Given a job has already been rolled up with a gpu cost
    When the same job's rollup write is attempted again
    Then the daily rollup gpu cost is unchanged

  Scenario: Rollups are read without scanning the jobs table
    Given thirty days of rollups exist for a site
    When the operator requests the cost summary for that site
    Then the summary reflects exactly the rollup records
