Feature: The AWS Batch fallback worker
  The fallback workflow starts a GPU container with a single job's worker
  token. The worker redeems the token for the job's text and voice, claims
  the job, renders it, uploads the audio, and marks the job done.

  Scenario: A Batch worker whose job already finished exits cleanly
    A local worker can finish the job while the GPU container is still
    starting. Finishing a job revokes its worker token, so redeeming it
    returns 404; the Batch worker has nothing left to do.

    Given the Auritus API reports the worker token for the job as not found
    When the Batch worker starts for that job
    Then the Batch worker exits successfully without claiming the job

  Scenario: A Batch worker whose speech backend is unavailable fails the job
    The GPU image can lack a backend's model libraries. The backend then
    raises BackendUnavailable instead of producing audio, and the Batch
    worker must release the job as failed rather than leave it claimed.

    Given the Auritus API has a "kokoro" job for voice "af_heart"
    And the speech model libraries are not installed
    When the Batch worker starts for that job
    Then the Batch worker marks the job failed because "kokoro" is unavailable
    And the Batch worker does not mark the job done
