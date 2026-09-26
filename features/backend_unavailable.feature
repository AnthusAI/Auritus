Feature: Missing speech backends fail loudly
  A backend whose model libraries are missing, or that cannot run on this
  machine, raises BackendUnavailable. It never returns a stand-in tone that
  looks like a successful result.

  Scenario Outline: The library refuses when a backend's libraries are missing
    Given the speech model libraries are not installed
    When I try to synthesize "Hello" with voice "<backend>:default"
    Then a BackendUnavailable error names "<backend>" and a missing module

    Examples:
      | backend    |
      | chatterbox |
      | higgs      |
      | fish       |
      | kokoro     |
      | qwen       |
      | f5         |

  Scenario Outline: Off Apple Silicon, backends use PyTorch and fail loudly without it
    Given this machine is not Apple Silicon
    And the speech model libraries are not installed
    When I try to synthesize "Hello" with voice "<backend>:default"
    Then a BackendUnavailable error names "<backend>" and a missing module

    Examples:
      | backend    |
      | chatterbox |
      | higgs      |
      | fish       |
      | kokoro     |
      | qwen       |
      | f5         |
