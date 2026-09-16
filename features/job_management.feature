Feature: Deleting a generated audio job

  Scenario: Operator deletes a completed job and its audio
    Given a job exists with status "done" and a stored audio object
    When the operator deletes the job by content hash
    Then the job record is removed
    And the audio object is removed from the audio bucket
    And requesting that job returns not found

  Scenario: Deleting a job that does not exist
    When the operator deletes a content hash with no job record
    Then the response is not found
    And no audio object is removed

  Scenario: Deleting a job requires operator authentication
    Given a job exists with status "done"
    When a caller presents only a site key and deletes the job
    Then the response is forbidden
    And the job record still exists
