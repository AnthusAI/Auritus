Feature: A named voice that cannot be found fails the job
  Cloning backends (Fish, Chatterbox, F5) speak in a voice taken from a
  reference recording. When a request names a voice, such as "serious", and
  no recording for it can be found, the request fails with VoiceNotFound,
  which names the voice and where it looked. It never substitutes a stock
  voice and reports success, and the check runs before any model loads.
  A request for the default voice ("default", the backend's own default id,
  or no voice at all) still speaks with the backend's stock voice.

  Scenario Outline: A named voice fails when no voices folder is configured
    Given no voices folder is configured
    And the speech model libraries are not installed
    When I try to synthesize "Hello" with voice "<backend>:serious"
    Then a VoiceNotFound error names "serious" and says no voices folder is configured
    And no speech was returned

    Examples:
      | backend    |
      | fish       |
      | chatterbox |
      | f5         |

  Scenario Outline: Off Apple Silicon a named voice fails the same way
    Given this machine is not Apple Silicon
    And no voices folder is configured
    And the speech model libraries are not installed
    When I try to synthesize "Hello" with voice "<backend>:serious"
    Then a VoiceNotFound error names "serious" and says no voices folder is configured
    And no speech was returned

    Examples:
      | backend    |
      | fish       |
      | chatterbox |
      | f5         |

  Scenario Outline: A named voice fails when the voices folder lacks it
    Given a voices folder containing "narrator.wav" and "narrator.txt"
    And the speech model libraries are not installed
    When I try to synthesize "Hello" with voice "<backend>:serious" from that folder
    Then a VoiceNotFound error names "serious" and that voices folder
    And no speech was returned

    Examples:
      | backend    |
      | fish       |
      | chatterbox |
      | f5         |

  Scenario Outline: A named voice in the voices folder is the one spoken
    Given a voices folder containing "serious.wav" and "serious.txt"
    And the cloning speech models are stubbed
    When I try to synthesize "Hello" with voice "<backend>:serious" from that folder
    Then the stubbed model spoke with that folder's "serious.wav"

    Examples:
      | backend    |
      | fish       |
      | chatterbox |
      | f5         |

  Scenario Outline: The default voice still speaks with the stock voice
    Given no voices folder is configured
    And the cloning speech models are stubbed
    When I try to synthesize "Hello" with voice "<voice>"
    Then the stubbed model spoke with the stock voice

    Examples:
      | voice               |
      | fish                |
      | fish:default        |
      | fish:narrator       |
      | chatterbox          |
      | chatterbox:default  |
      | chatterbox:narrator |
      | f5                  |
      | f5:default          |

  Scenario: The Batch worker fails a job whose named voice is not in its image
    Given the Auritus API has a "fish" job for voice "serious"
    And the Batch image has no reference voices
    And the cloning speech models are stubbed
    When the Batch worker starts for that job
    Then the Batch worker marks the job failed with a reason naming "serious"
    And the Batch worker does not mark the job done

  Scenario: The Batch worker still completes a default-voice job
    Given the Auritus API has a "fish" job for voice "narrator"
    And the Batch image has no reference voices
    And the cloning speech models are stubbed
    When the Batch worker starts for that job
    Then the Batch worker marks the job done

  Scenario: The local worker fails a job whose named voice is not in its folder
    Given a claimable "fish" job for voice "serious" with an empty voices folder
    And the cloning speech models are stubbed
    When the worker runs a single poll cycle
    Then the job is marked failed with the worker as owner
    And the failure reason names "serious"

  Scenario: The local worker still completes a default-voice job
    Given a claimable "fish" job for voice "narrator" with an empty voices folder
    And the cloning speech models are stubbed
    When the worker runs a single poll cycle
    Then the job is marked done
