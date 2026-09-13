Feature: Release publish gate
  GitHub releases on main must not fail the workflow while PyPI trusted
  publishing is still disabled. Operators enable publish with a repository
  variable.

  Scenario: PyPI publish is skipped unless explicitly enabled
    Given the release workflow file
    Then the PyPI publish step requires AURITUS_PUBLISH_PYPI
