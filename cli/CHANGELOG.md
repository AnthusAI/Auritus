# CHANGELOG

<!-- version list -->

## v0.6.6 (2026-09-13)

### Bug Fixes

- Show example player chrome before POST /jobs returns
  ([`d1c4d2d`](https://github.com/AnthusAI/Auritus/commit/d1c4d2d24a21750fc9c21a2f84aa726e44a9bb6a))


## v0.6.5 (2026-09-13)

### Bug Fixes

- Put example players above the article with visible chrome
  ([`c595319`](https://github.com/AnthusAI/Auritus/commit/c595319ebb85d4d64e9661aa51056cb385f2d96f))

### Chores

- Stop tracking Playwright test-results
  ([`75fa984`](https://github.com/AnthusAI/Auritus/commit/75fa984d08d24c6c5286b0b65adf62ade971fd32))

### Testing

- Attach-only locators for live example Playwright
  ([`49028e3`](https://github.com/AnthusAI/Auritus/commit/49028e3dcecc0637bbd9f84a123d1cf312a8c4ef))


## v0.6.4 (2026-09-13)

### Bug Fixes

- Bake Kokoro into Batch image and harden worker once-check
  ([`c8ac819`](https://github.com/AnthusAI/Auritus/commit/c8ac8198683fdb22df8bdfb20b8cbd403d72ca50))

- Declare Batch GPU jobs with VCPU and MEMORY resource requirements
  ([`76e579a`](https://github.com/AnthusAI/Auritus/commit/76e579a925ff6b5b03662168d715a253e45fe8b9))

- Default cloud TTS backend to Kokoro
  ([`c0ae28f`](https://github.com/AnthusAI/Auritus/commit/c0ae28f94fecf2ebc2daeb67e94009446fd5660e))

- Give each example unique speech and re-boot the player
  ([`e5e4f94`](https://github.com/AnthusAI/Auritus/commit/e5e4f941f2e7c0381d28c756ca43da8d097a2b62))

- Omit Content-Type on Batch S3 upload
  ([`d3b7ffc`](https://github.com/AnthusAI/Auritus/commit/d3b7ffca2b41a0560991891aff050779a6f4f49c))

- Size Batch GPU jobs to fit g4dn.xlarge
  ([`2af454e`](https://github.com/AnthusAI/Auritus/commit/2af454e410831e79e7d597a3a89c3436af7b3b2e))

- Wire worker --once as a real bool under Click 8.5
  ([`78d9545`](https://github.com/AnthusAI/Auritus/commit/78d95459092690502b23b56d63cf51d550b67222))

- **cli**: Cognito USER_PASSWORD_AUTH login
  ([`85315a0`](https://github.com/AnthusAI/Auritus/commit/85315a08311344ff3782b057e3bd4d2fb632b1b3))

- **cli**: Run token refresh in default CI
  ([`a8a2bce`](https://github.com/AnthusAI/Auritus/commit/a8a2bce9ef29e6b301f0f6b7e1748bdada8f0c9f))

- **tts**: Default Kokoro voice to af_heart
  ([`1fe0011`](https://github.com/AnthusAI/Auritus/commit/1fe00110be038e8525bc55f09e7193ed0c5578f8))

- **tts**: Load Qwen CustomVoice and default to Ryan
  ([`615d48c`](https://github.com/AnthusAI/Auritus/commit/615d48c865afbdc6ee564fcc06970cc9056f8b54))

- **tts**: Scope af_heart default voice to Kokoro backend
  ([`bc575c3`](https://github.com/AnthusAI/Auritus/commit/bc575c3e1b4fc9c0b20272f0f806c24cf71f12fb))

### Code Style

- Ruff I001 on cli_login_steps imports
  ([`5b711e7`](https://github.com/AnthusAI/Auritus/commit/5b711e769b8ebebc93d9866a5693dc8d109f7da9))

- Ruff I001 on cli_login_steps imports
  ([`8873f5e`](https://github.com/AnthusAI/Auritus/commit/8873f5e705ed1f9d5fd3ebb1c4d0d064ea331447))

- Satisfy CI ruff I001 on CDK imports
  ([`195b81d`](https://github.com/AnthusAI/Auritus/commit/195b81d6fdd1d5c790da12703772036d67df6b45))

### Documentation

- Deploy before login; document Cognito password CLI auth
  ([`2b81d28`](https://github.com/AnthusAI/Auritus/commit/2b81d2848596d159620c854e026c2c7f511f576d))

- Describe Cognito password CLI login
  ([`fde318a`](https://github.com/AnthusAI/Auritus/commit/fde318a55c5ce5ef348c03b3ed4d0b609dfb49e3))

- Fix acceptance and site self-hosting login steps
  ([`da6faa9`](https://github.com/AnthusAI/Auritus/commit/da6faa98b33d752380bf28efc38cc8b49e3f8131))

### Testing

- Align login Gherkin with file-based token cache
  ([`19dbd31`](https://github.com/AnthusAI/Auritus/commit/19dbd31d58aed443ef9abbc1252a65ea258814a3))

- Assert Kokoro speech wiring in Playwright
  ([`d1d6534`](https://github.com/AnthusAI/Auritus/commit/d1d65347dc1f67dc6642ed8781f276c664361716))

- Prove Qwen and Kokoro registry without loading weights
  ([`82b0b3f`](https://github.com/AnthusAI/Auritus/commit/82b0b3f5c89e71363958d51805be37a06d600b2e))

- Restore Kokoro default-voice Gherkin scenario
  ([`cd0be00`](https://github.com/AnthusAI/Auritus/commit/cd0be00ea65d720641579bb924987c139edf51d8))

- Wait up to 120s for Kokoro job in Playwright
  ([`15d4d41`](https://github.com/AnthusAI/Auritus/commit/15d4d412f5217e2aab82fd3e4d296d27e6b60201))


## v0.6.3 (2026-09-13)

### Bug Fixes

- Default to Kokoro speech and scope example narration
  ([`85592f8`](https://github.com/AnthusAI/Auritus/commit/85592f891e5d4f964891995a6c68c2bd8dfacc9c))

- Make TTS backend imports lazy so CI needs no numpy
  ([`cd6d4c7`](https://github.com/AnthusAI/Auritus/commit/cd6d4c702261761dbf0078deaaacc04ddaafbad8))

### Chores

- **kanbus**: Close Kokoro demo default fix task
  ([`9c07342`](https://github.com/AnthusAI/Auritus/commit/9c07342fde761d0c62f2d2e7bf3fbb02a2f9ef1d))

### Code Style

- Black-format content_hash_steps for CI
  ([`f00f334`](https://github.com/AnthusAI/Auritus/commit/f00f334959d4aec48de45854a66d3b4d166a1e5e))

### Testing

- Expect Kokoro as default TTS backend
  ([`9381e9e`](https://github.com/AnthusAI/Auritus/commit/9381e9e5e990a1f3d0cae3e3bc0cc38a15e9e917))


## v0.6.2 (2026-09-12)

### Bug Fixes

- Exclude tts_backend from content hash for backend portability
  ([`b688909`](https://github.com/AnthusAI/Auritus/commit/b688909c6604ad19b52aec69a3781f8ce33019f2))


## v0.6.1 (2026-09-12)

### Bug Fixes

- Default embed tts_backend to kokoro
  ([`453e653`](https://github.com/AnthusAI/Auritus/commit/453e653b0594d6468db2702dbf900a7ec78f6e66))

- Default TTS backend to Kokoro, file-based token storage, continuous worker
  ([`d7d5ca6`](https://github.com/AnthusAI/Auritus/commit/d7d5ca6603a92c0e7c01a9b50259ca7275db06ff))

### Chores

- **kanbus**: Commit board state (issues)
  ([`d2e95cd`](https://github.com/AnthusAI/Auritus/commit/d2e95cdb3301b5c07ff314643ba5139b1e5cbcdf))

- **kanbus**: Commit board state (issues)
  ([`f790da8`](https://github.com/AnthusAI/Auritus/commit/f790da8e51a76bc481e0e88011bf3c148ed21f8f))


## v0.6.0 (2026-09-12)

### Bug Fixes

- Mlx-audio integration, worker-image TTS backends, test fixes
  ([`06f8bf5`](https://github.com/AnthusAI/Auritus/commit/06f8bf5ae3d50454ab265313de6467669638a8e8))

### Features

- Integrate mlx-audio for Apple Silicon TTS generation
  ([`6eda1bd`](https://github.com/AnthusAI/Auritus/commit/6eda1bd45bb7831f1381a923d54e905ca6d786c4))


## v0.5.0 (2026-09-12)

### Bug Fixes

- Check Bearer token in _check_job_token for Batch worker auth
  ([`da27382`](https://github.com/AnthusAI/Auritus/commit/da2738242efa0371d703ce59c86013238888c0a8))

- Move done and presign-upload to public routes for worker auth
  ([`d6773dd`](https://github.com/AnthusAI/Auritus/commit/d6773dd15a6785408eb1a6bb247dbf081f591b0e))

- Move worker routes (claim, done, presign) to public group; keep claimable behind auth
  ([`6767a5f`](https://github.com/AnthusAI/Auritus/commit/6767a5fc5f21366b15c65c2d8bf320f3eaf430f2))

- Remove Content-Type header from S3 upload to avoid signature mismatch
  ([`7c8db8b`](https://github.com/AnthusAI/Auritus/commit/7c8db8b4a54e586260fd4947d4a55aa769bb3fdf))

- Remove debug print, fix black formatting on claim route
  ([`f0a6107`](https://github.com/AnthusAI/Auritus/commit/f0a6107ecc3333ac7068560e4e8d232db5f55130))

### Chores

- **kanbus**: Commit board state (issues)
  ([`8b1c7c2`](https://github.com/AnthusAI/Auritus/commit/8b1c7c2a4ed4eda87de76566136abb29a698463d))

### Features

- Add redeem route and job token auth for presign-upload
  ([`0177ff7`](https://github.com/AnthusAI/Auritus/commit/0177ff7b270928d6ef7a797b9fbcc055cf0f8d1e))


## v0.4.7 (2026-09-12)

### Bug Fixes

- Install only Kokoro in worker image (MVP); other backends deferred due to dependency conflicts
  ([`25de41f`](https://github.com/AnthusAI/Auritus/commit/25de41fc121388c8fda1cee7155993a0fa2f51b8))


## v0.4.6 (2026-09-12)

### Bug Fixes

- Install typing_extensions and setuptools before main deps
  ([`b661b35`](https://github.com/AnthusAI/Auritus/commit/b661b35d07fa993d8becc156423e5fd0ef71dc07))


## v0.4.5 (2026-09-12)

### Bug Fixes

- Install numpy in separate Docker layer before other deps
  ([`a5517b2`](https://github.com/AnthusAI/Auritus/commit/a5517b2478902a08953b542879b04f46be8985c8))


## v0.4.4 (2026-09-12)

### Bug Fixes

- Install numpy first in worker image for build deps
  ([`57ea78c`](https://github.com/AnthusAI/Auritus/commit/57ea78cb9d95856de00a02f0bb062d7429c6376e))


## v0.4.3 (2026-09-12)

### Bug Fixes

- Relax fish-speech version constraint for pip install
  ([`f0e6cd6`](https://github.com/AnthusAI/Auritus/commit/f0e6cd659421a7f3dc6d6560a8fc7bc41453223e))

### Chores

- **kanbus**: Commit board state (issues)
  ([`188f53a`](https://github.com/AnthusAI/Auritus/commit/188f53a04195ccedd38a3989076cd40b31907786))


## v0.4.2 (2026-09-12)

### Bug Fixes

- Correct ECR login inputs for amazon-ecr-login@v2
  ([`232316b`](https://github.com/AnthusAI/Auritus/commit/232316b367d238e18498d5c9ec3a17c0d8edadc2))


## v0.4.1 (2026-09-12)

### Bug Fixes

- Use dedicated IAM role for worker image ECR push
  ([`2632fe2`](https://github.com/AnthusAI/Auritus/commit/2632fe293c446e3dbbdb80559832034efac8eeef))


## v0.4.0 (2026-09-12)

### Bug Fixes

- Remove unused noqa from test_tts, verify all tests pass
  ([`7a3a3a5`](https://github.com/AnthusAI/Auritus/commit/7a3a3a5b5d82fc054b404d66ea39db3defa06160))

- Worker token refresh, player UI, TTS tone stub, black formatting
  ([`3252fe2`](https://github.com/AnthusAI/Auritus/commit/3252fe27ab4a266d95b9ec933fa3ff0458d97e4f))

### Chores

- **kanbus**: Commit board state (issues)
  ([`97bef1f`](https://github.com/AnthusAI/Auritus/commit/97bef1fbce07788a598495599f86a09c63bbb9a6))

### Continuous Integration

- Add workflow to build and push worker image to ECR
  ([`3daf65c`](https://github.com/AnthusAI/Auritus/commit/3daf65c291cb3df88ee23cb0986890b2b2d5c7e0))

### Features

- Add Fish Speech, Coqui XTTS-v2, and Bark TTS backends
  ([`461e784`](https://github.com/AnthusAI/Auritus/commit/461e784863b09c969e9e9d444b29a81064a18f07))

- Integrate Kokoro-82M as first real TTS backend
  ([`9f55d18`](https://github.com/AnthusAI/Auritus/commit/9f55d18a69cccfd307c4c4a22f84c328377faf93))


## v0.3.3 (2026-09-12)

### Bug Fixes

- Presign-upload route, S3 presigned GET URLs, remove Content-Type on upload
  ([`a088ed8`](https://github.com/AnthusAI/Auritus/commit/a088ed8a758861e6bc39e204ecb31b85e1e800d6))

### Chores

- **kanbus**: Commit board state (issues)
  ([`22252f0`](https://github.com/AnthusAI/Auritus/commit/22252f098717cda3ef5076eab3e7bc7fe3685f51))


## v0.3.2 (2026-09-12)

### Bug Fixes

- Use content_hash from embed if provided (FNV-1a vs SHA-256 mismatch)
  ([`73e7b12`](https://github.com/AnthusAI/Auritus/commit/73e7b12f78584129baccd1508c2e165199fa0418))


## v0.3.1 (2026-09-12)

### Bug Fixes

- Add data-auritus-api to Script tag so embed uses live API
  ([`640a535`](https://github.com/AnthusAI/Auritus/commit/640a535de122633c9125cb5cd9eb37cfa1cf13d3))


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
