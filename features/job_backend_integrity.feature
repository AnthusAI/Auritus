@job_backend_integrity
Feature: Job backend integrity on content hash collision

  Scenario: A job keeps its backend and audio when a colliding hash arrives
    Given a job exists with backend "kokoro", status "done", and stored audio
    When a job is created with that explicit content hash and backend "higgs"
    Then the colliding job is rejected as a content hash mismatch
    And the stored job still has backend "kokoro"
    And the stored job still points at the original audio
