Feature: Admin unfiltered job listing returns the genuinely most recent jobs

  GET /admin/jobs with no status filter is the default "all jobs" dashboard
  view. It must return the most recently created jobs first, drawn from
  every status, not merely whatever a size-limited internal scan happened
  to read before stopping.

  Scenario: Newest jobs are returned first even when they share one status
    Given eight jobs spread across every status with staggered creation times
    And the three most recently created jobs all have status "done"
    When the operator requests the unfiltered job list with limit 3
    Then the response contains exactly the 3 most recently created jobs
    And those jobs are ordered from newest to oldest

  Scenario: Paging through the unfiltered listing returns every job exactly once
    Given twelve jobs spread across every status with staggered creation times
    When the operator pages through the unfiltered job list with limit 5
    Then every page but the last contains exactly 5 jobs
    And the jobs across all pages are exactly the twelve jobs with no duplicates
    And the jobs across all pages appear in order from newest to oldest
