# CHANGELOG

<!-- version list -->

## v0.3.0 (2026-09-12)

### Features

- Wire embed to live API with data-auritus-api attribute
  ([`2f70678`](https://github.com/AnthusAI/Auritus/commit/2f706781f720b3fcab01429157a42fe1a14ab6ba))


## v0.2.5 (2026-09-12)

### Bug Fixes

- Revert authorizer to shape check, remove Lambda layer, fix test
  ([`d0d8ab4`](https://github.com/AnthusAI/Auritus/commit/d0d8ab4f7f81f6a0629141a35d5d015e0d0085ef))

### Chores

- **kanbus**: Commit board state (issues)
  ([`acaa056`](https://github.com/AnthusAI/Auritus/commit/acaa056da6a0e8d47c90d51f9a1e7356bb09de1c))


## v0.2.4 (2026-09-12)

### Bug Fixes

- Remove shebang from app.py and fix import sorting
  ([`58fd0ef`](https://github.com/AnthusAI/Auritus/commit/58fd0ef9818f7ce9d8d90d61cae62034664b97e4))


## v0.2.3 (2026-09-12)

### Bug Fixes

- Restore cross-step import and ignore F401 for behave step files
  ([`683f528`](https://github.com/AnthusAI/Auritus/commit/683f5282ccfb7946d43edafd55139c2e2ad73bf1))


## v0.2.2 (2026-09-12)

### Bug Fixes

- Remove unused noqa and fix UP045 Optional types
  ([`3bf2125`](https://github.com/AnthusAI/Auritus/commit/3bf212538705e245d81c36333fa850cba71cc8dd))


## v0.2.1 (2026-09-12)

### Bug Fixes

- Ignore B008 for Typer, fix RUF013 Optional types, update ruff config
  ([`d9803e0`](https://github.com/AnthusAI/Auritus/commit/d9803e0858d4e63d6d73b80ebfdb998505560f0f))


## v0.2.0 (2026-09-12)

### Features

- Add Lambda layer for JWKS verification and fix all ruff issues
  ([`7046c7c`](https://github.com/AnthusAI/Auritus/commit/7046c7c6e71a32b6ee6898b511948c9870ffdd93))


## v0.1.6 (2026-09-12)

### Bug Fixes

- Resolve ruff I001 import sorting across all Python files
  ([`8c01dee`](https://github.com/AnthusAI/Auritus/commit/8c01dee356250ac64b6c213bbd20329a3d05bfd2))


## v0.1.5 (2026-09-12)

### Bug Fixes

- Resolve all ruff BLE001 and RUF022 errors across CLI and worker-image
  ([`3065c0c`](https://github.com/AnthusAI/Auritus/commit/3065c0cc930cf2b3db91a91756b991ed823b1a2b))

### Testing

- Update authorizer test for stdlib shape-check version
  ([`50d552c`](https://github.com/AnthusAI/Auritus/commit/50d552c3ace30c25bc1110742448e6bac5647c48))


## v0.1.4 (2026-09-12)

### Bug Fixes

- Revert authorizer to shape check for Lambda runtime compatibility
  ([`068c6f6`](https://github.com/AnthusAI/Auritus/commit/068c6f67d9702e90779d8bec08476e21383649f9))

### Chores

- **kanbus**: Commit board state (issues)
  ([`a202d46`](https://github.com/AnthusAI/Auritus/commit/a202d462883862240dc80c504e098d1a16aab651))

- **kanbus**: Commit board state (issues)
  ([`660b3f8`](https://github.com/AnthusAI/Auritus/commit/660b3f8ae53f8ca6442f736281ba01ab799993c9))


## v0.1.3 (2026-09-11)

### Bug Fixes

- Point Amplify artifacts to out/ for Next.js static export
  ([`b546330`](https://github.com/AnthusAI/Auritus/commit/b5463302ddcf5541c2973a594a29b87937d37646))


## v0.1.2 (2026-09-11)

### Bug Fixes

- Add output: export to next.config.js for Amplify static hosting
  ([`35850ef`](https://github.com/AnthusAI/Auritus/commit/35850ef07edf43a4550d8ea57f26bbc41e73c40e))

### Chores

- **kanbus**: Commit board state (issues)
  ([`40e9911`](https://github.com/AnthusAI/Auritus/commit/40e991175b9d3d53ce539d129e7b9962583373ee))

### Code Style

- Apply black formatting to authorizer handler
  ([`d021783`](https://github.com/AnthusAI/Auritus/commit/d021783cc89ce4c74d9af74b8b22f2795bdb361a))


## v0.1.1 (2026-09-11)

### Bug Fixes

- Use Amplify monorepo format with appRoot for site
  ([`dac9a31`](https://github.com/AnthusAI/Auritus/commit/dac9a3106f02527091e639086fdd38df669aa31d))

### Chores

- Add root-level amplify.yml for monorepo site build
  ([`50a9699`](https://github.com/AnthusAI/Auritus/commit/50a969970601d7400d23be55bb4436cd7c0b78c6))

- Add root-level amplify.yml for monorepo site build
  ([`10d0b43`](https://github.com/AnthusAI/Auritus/commit/10d0b43a6f560d9f2d75aabb3d05f2e6b18d8e51))


## v0.1.0 (2026-09-11)

- Initial Release
