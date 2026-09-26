Feature: Re-keying stored jobs to the canonical content hash
  Earlier embeds keyed jobs by a 32-bit FNV-1a hash they computed in the
  browser. The API now computes the SHA-256 content hash itself and rejects
  any other hash, so finished jobs move to their canonical hash and reuse
  their generated audio rather than regenerating it.

  The move happens in two phases so pages running the old embed keep playing
  until the new embed and API are live. The copy phase writes each finished
  job under its canonical hash and leaves the legacy row in place. After the
  release, the removal phase deletes legacy rows whose canonical copy
  records that it was migrated from them. Jobs still in flight are never
  copied, because the fallback workflow and the Batch worker's job token
  refer to their key.

  Scenario: A finished job keyed by a legacy hash is copied to its canonical hash
    Given a "done" job stored under the legacy hash "2caf28aa" with text "Press play." and stored audio
    When the content hash copy runs with apply
    Then the job is stored under the canonical hash of "Press play."
    And the migrated job keeps its audio and records it was migrated from "2caf28aa"
    And a job is still stored under "2caf28aa"

  Scenario: A dry run changes nothing
    Given a "done" job stored under the legacy hash "2caf28aa" with text "Press play." and stored audio
    When the content hash copy runs without apply
    Then the migration reports 1 job to copy
    And no job is stored under the canonical hash of "Press play."

  Scenario: Jobs still in flight keep their key
    Given a "pending" job stored under the legacy hash "01355d8a" with text "Still rendering." and no audio
    When the content hash copy runs with apply
    Then no job is stored under the canonical hash of "Still rendering."
    And the migration reports 1 job skipped as in flight

  Scenario: An existing canonical job is never overwritten
    Given a "done" job stored under the legacy hash "2caf28aa" with text "Press play." and stored audio
    And a "done" job already stored under the canonical hash of "Press play."
    When the content hash copy runs with apply
    Then the canonical job is unchanged
    And the migration reports 1 job skipped as already canonical elsewhere

  Scenario: Legacy rows are removed once their canonical copy exists
    Given a "done" job stored under the legacy hash "2caf28aa" with text "Press play." and stored audio
    And the content hash copy has run with apply
    When the legacy row removal runs with apply
    Then no job is stored under "2caf28aa"
    And the job is stored under the canonical hash of "Press play."

  Scenario: Legacy rows without a migrated copy are kept
    Given a "done" job stored under the legacy hash "2caf28aa" with text "Press play." and stored audio
    And a "done" job already stored under the canonical hash of "Press play."
    When the legacy row removal runs with apply
    Then a job is still stored under "2caf28aa"
