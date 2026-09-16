Feature: Estimated cost per job

  Scenario: A locally processed job has no GPU cost but has a platform cost
    Given a local job is marked done
    Then the job gpu cost is zero
    And the job platform cost is greater than zero

  Scenario: A job records the rate card it was costed against
    Given a local job is marked done
    Then the job records a cost rate and a rate card version

  Scenario: A failed job is still costed
    Given a local job is marked failed
    Then the job platform cost is greater than zero
