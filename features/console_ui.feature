Feature: Web console dashboard and job explorer
  Operators access an authenticated web console to monitor real-time job
  activity, view KPI metrics, inspect generation timelines, and control queues.

  Scenario: Dashboard displays KPI metrics
    Given the operator is logged into the web console
    When the dashboard overview loads
    Then the total job count is displayed
    And the worker race split is displayed
    And the Batch queue status is displayed

  Scenario: Job explorer displays filterable job rows
    Given the operator is on the jobs page
    When filtering by status "done"
    Then the table lists only completed jobs
    And each job row displays the worker attribution

  Scenario: Job detail page renders audio playback control
    Given a completed job with an audio URL
    When viewing the job detail page
    Then an audio player control is rendered
    And the synthesis duration is displayed

  Scenario: Job explorer navigates pages with pagination controls
    Given the operator is on the jobs page
    When navigating to the next page of jobs
    Then the second page of jobs is displayed
    And the previous page button is enabled

