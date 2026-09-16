Feature: Local worker crash recovery

  If TTS generation raises after a job is claimed -- most often because an
  optional backend dependency is missing -- the local worker must release
  the claim by marking the job failed instead of leaving it stuck in
  "claimed" forever. GET /jobs/claimable only ever returns pending jobs (or
  claimed jobs whose deadline has expired), so a claimed job that nothing
  ever marks failed or done is invisible to every future worker, local or
  Batch, for good.

  Scenario: Generation failure releases the claim instead of leaving it stuck
    Given a claimable job that a local worker will claim
    And the worker's TTS backend raises an exception during generation
    When the worker runs a single poll cycle
    Then the job is marked failed with the worker as owner
    And the worker does not crash

  Scenario: Successful generation still completes the job as before
    Given a claimable job that a local worker will claim
    And the worker's TTS backend generates audio successfully
    When the worker runs a single poll cycle
    Then the job is marked done
