Feature: Job telemetry and worker race attribution
  Jobs in Auritus must preserve worker attribution (local vs batch), execution
  durations, and explicit failure status so operators can observe generation
  health and performance.

  Scenario: Local worker claim records local worker type and claim time
    Given a pending job with content hash "job-local-telemetry-1"
    When worker "local:node-1:abcdef" claims the job
    Then the job status is "claimed"
    And the job worker_type is "local"
    And the job claimed_by is "local:node-1:abcdef"
    And the job has a claimed_at timestamp

  Scenario: Batch worker claim records batch worker type and claim time
    Given a pending job with content hash "job-batch-telemetry-1"
    When worker "batch:job-uuid-1234" claims the job
    Then the job status is "claimed"
    And the job worker_type is "batch"
    And the job claimed_by is "batch:job-uuid-1234"
    And the job has a claimed_at timestamp

  Scenario: Job completion preserves worker attribution and calculates duration
    Given a job claimed by "local:node-1:abcdef" with content hash "job-done-telemetry-1"
    When the job is marked done with audio key "audio/job-done.mp3"
    Then the job status is "done"
    And the job worker_type is "local"
    And the job claimed_by is "local:node-1:abcdef"
    And the job has a completed_at timestamp
    And the job duration_seconds is recorded

  Scenario: Worker failure marks job failed with error details
    Given a job claimed by "batch:job-uuid-5678" with content hash "job-fail-telemetry-1"
    When worker "batch:job-uuid-5678" reports failure with reason "Out of GPU memory"
    Then the job status is "failed"
    And the job worker_type is "batch"
    And the job error_message is "Out of GPU memory"
    And the job has a failed_at timestamp
