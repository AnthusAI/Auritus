Feature: Player playback restart
  Generated speech must start from the beginning when the listener activates
  Play after the clip has already finished.

  Scenario: Play after the clip ends starts from the beginning
    Given generated audio duration is 23 seconds
    And playback is at 23 seconds
    When the listener activates Play
    Then playback position is 0 seconds
