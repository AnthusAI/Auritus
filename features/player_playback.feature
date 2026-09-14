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

  Scenario: Player displays play icon when idle and pause icon while playing
    Given the player is mounted with ready audio
    When playback is idle
    Then the play button shows a play icon
    And the play button has label "Play"
    When playback is active
    Then the play button shows a pause icon
    And the play button has label "Pause"

  Scenario: Player formats clip duration and playback progress
    Given an audio clip with duration 143 seconds
    When 25 seconds of the clip have played
    Then the elapsed time displays "0:25"
    And the total duration displays "2:23"
