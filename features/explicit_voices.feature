Feature: Reference voices come only from an explicit folder
  Cloning backends read reference voices (<id>.wav plus <id>.txt) from a
  folder the caller names: the voices_dir argument, or else AURITUS_VOICES.
  Nothing is picked up from the current directory, the package's own
  location, or a container path, and there are no hidden aliases.

  Scenario: Listing voices reads only the named folder
    Given a voices folder containing "narrator.wav" and "narrator.txt"
    And the current directory contains "impostor.wav"
    When I list reference voices from that folder
    Then the listed voices are exactly "narrator"

  Scenario: A voice lying in the current directory is not used
    Given no voices folder is configured
    And the current directory contains "impostor.wav"
    When I resolve reference audio for "impostor"
    Then no reference audio is found

  Scenario: AURITUS_VOICES names the folder when no argument does
    Given AURITUS_VOICES points at a folder containing "narrator.wav" and "narrator.txt"
    When I resolve reference audio for "narrator"
    Then the reference is that folder's "narrator.wav"
    And the reference transcript is read from that folder's "narrator.txt"

  Scenario: There are no hidden voice aliases
    Given a voices folder containing "steve_jobs.wav" and "steve_jobs.txt"
    When I resolve reference audio for "steve" from that folder
    Then no reference audio is found

  Scenario: synthesize hands its voices folder to the backend
    Given a voices folder containing "narrator.wav" and "narrator.txt"
    When I synthesize "Hello" with voice "fake:narrator" from that folder
    Then the backend was given that voices folder

  Scenario: The local worker names the voices folder it uses
    Given worker config without a voices_dir
    When the worker's voices folder is resolved in "/srv/auritus"
    Then the worker voices folder is "/srv/auritus/voices"
