Feature: Forcing regeneration of already-generated audio

  Scenario: Operator regenerates a completed clip
    Given a completed job with stored audio for regeneration
    When the operator forces regeneration of that content hash
    Then the regenerated job status is "pending"
    And the previous audio object is removed from the audio bucket
    And the regenerated job has no audio url

  Scenario: Regeneration keeps the content hash stable
    Given a completed job for regeneration
    When the operator forces regeneration of that content hash
    Then the regenerated job keeps the same content hash

  Scenario: Regenerating a job that is already pending is rejected
    Given a pending job for regeneration
    When the operator forces regeneration of that content hash
    Then the response is a conflict
    And the regenerated job status remains "pending"

  Scenario: Regeneration issues a fresh job token
    Given a completed job with tracked token for regeneration
    When the operator forces regeneration of that content hash
    Then the regenerated job token is different from the previous token
