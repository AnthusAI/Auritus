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

  Scenario Outline: MLX-only backends refuse on machines without Apple Silicon
    Given this machine is not Apple Silicon
    When I try to synthesize "Hello" with voice "<backend>:default"
    Then a BackendUnavailable error names "<backend>" and says it needs Apple Silicon

    Examples:
      | backend    |
      | higgs      |
      | chatterbox |

  Scenario Outline: The Batch worker fails the job instead of faking audio
    Given the speech model libraries are not installed
    When the Batch worker's "<backend>" backend generates "Hello"
    Then the worker raises BackendUnavailable naming "<backend>"

    Examples:
      | backend    |
      | higgs      |
      | chatterbox |
      | fish       |
