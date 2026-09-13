Feature: Player playback
  Generated speech must start from the beginning when the listener activates
  Play after the clip has already finished. Play while audio is still arriving
  must start the clip as soon as it is ready.

  Scenario: Play after the clip ends starts from the beginning
    Given generated audio duration is 23 seconds
    And playback is at 23 seconds
    When the listener activates Play
    Then playback position is 0 seconds

  Scenario: Play while waiting starts when audio is ready
    Given the player is waiting for audio
    When the listener activates Play
    And the clip becomes ready
    Then playback starts
