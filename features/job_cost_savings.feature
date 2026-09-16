Feature: Savings from local worker processing

  Scenario: A local job falls back to its own duration when no Batch average exists yet
    Given no Batch samples exist for a backend
    When a local job using that backend completes
    Then the job avoided cost is based on its own duration
    And the job avoided cost basis is the local duration fallback

  Scenario: A local job uses the Batch average once samples exist
    Given Batch samples exist for a backend with a known average billed time
    When a local job using that backend completes
    Then the job avoided cost is based on the Batch average
    And the job avoided cost basis is the batch average

  Scenario: A Batch job has no avoided cost
    Given a job was claimed by a Batch worker
    When the job completes
    Then the job avoided cost is zero

  Scenario: Savings accumulate in the daily rollup
    Given two local jobs complete for a site
    Then the daily rollup avoided cost is the sum of both jobs avoided costs

  Scenario: A retried backend-timing sample does not double count
    Given a Batch job's timing has already been sampled into the backend average
    When the same job's timing sample is attempted again
    Then the backend average sample count is unchanged
