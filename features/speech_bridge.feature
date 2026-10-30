Feature: A persistent offline speech bridge
  A host can exchange versioned requests with one local speech process.
  The fake backend is explicitly simulated and is not evidence of real speech.

  Scenario: Capabilities and recoverable errors share a process
    Given a simulated speech bridge process
    When it receives capabilities, synthesis, an invalid request, and synthesis
    Then it returns four correlated JSON responses and exits cleanly
    And the simulated audio and metadata have verified sample counts and digests

  Scenario: Kokoro readiness reflects local model and selected voice files
    Given a simulated local Kokoro cache
    When the bridge inspects complete and incomplete cached snapshots
    Then it reports readiness only for the complete snapshot

  Scenario: Invalid fields and unsafe output paths are recoverable
    Given a simulated speech bridge process
    When it receives invalid fields and unsafe output paths
    Then each request receives an invalid request response

  Scenario: A model diagnostic cannot corrupt the response stream
    Given an injected simulated synthesis that prints a diagnostic
    When a synthesis request runs through the bridge
    Then stdout contains only a valid response and the diagnostic goes to stderr

  Scenario: Injected Kokoro results preserve real-model provenance without inference
    Given a simulated cached Kokoro request and injected speech result
    When the bridge publishes the injected speech
    Then the result retains model revision and is marked non-simulated

  Scenario: Cache discovery never requests network access
    Given a local-only cache resolver spy
    When the bridge resolves a cached snapshot
    Then the resolver requests local files only

  Scenario: A changed cached snapshot replaces the loaded model and voice
    Given two simulated Kokoro snapshots
    When successive requests select each snapshot
    Then each request binds its own model and voice files

  Scenario: Native model diagnostics cannot corrupt the response stream
    Given an injected model that writes directly to stdout
    When its synthesis request runs in a bridge process
    Then the native diagnostic goes to stderr and stdout contains only JSON

  Scenario: An interrupted publication exposes no partial speech artifacts
    Given an empty segment directory and simulated speech
    When publication fails before its atomic commit
    Then the segment directory has no published artifacts

  Scenario: Simulated MLX Kokoro loads the selected local model and voice
    Given simulated MLX Kokoro dependencies and selected local paths
    When the Kokoro backend generates simulated MLX audio
    Then the model and voice loaders receive those selected paths

  Scenario: Simulated PyTorch Kokoro loads the selected local model and voice
    Given simulated PyTorch Kokoro dependencies and selected local paths
    When the Kokoro backend generates simulated PyTorch audio
    Then the model and voice loaders receive those selected paths

  Scenario: Distinct pinned Kokoro model and voice revisions enable cache identity
    Given a simulated Kokoro capability with distinct pinned model and voice revisions
    When the host checks the simulated Kokoro capability
    Then caching is enabled and both revisions are reported

  Scenario: An unknown Kokoro voice revision disables cache identity
    Given a simulated Kokoro capability with an unknown voice revision
    When the host checks the simulated Kokoro capability
    Then caching is disabled because the voice revision is unknown

  Scenario: Simulated speech provenance retains distinct pinned voice identity
    Given a simulated Kokoro capability with distinct pinned model and voice revisions
    When the host synthesizes simulated speech using that capability
    Then the speech provenance permits caching and retains both revisions

  Scenario: An unknown Kokoro model revision disables cache identity
    Given a simulated Kokoro capability with an unknown model revision
    When the host checks the simulated Kokoro capability
    Then caching is disabled because the model revision is unknown
