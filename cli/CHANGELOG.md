# CHANGELOG

<!-- version list -->

## v0.23.1 (2026-09-19)


## v0.23.0 (2026-09-19)

### Bug Fixes

- **tts**: Address PR review findings on voice resolution and cuda routing
  ([`02852df`](https://github.com/AnthusAI/Auritus/commit/02852df707a09cf70d5d9b8de76b2f09a7457aba))

### Chores

- Close auritus-13b752 (wire serious voice reference audio into cloning models)
  ([`a20283b`](https://github.com/AnthusAI/Auritus/commit/a20283b0f9394208d2298d7ce7213ccd2bbfc53b))

- **board**: Close pricing card hrule alignment chore
  ([`479f42d`](https://github.com/AnthusAI/Auritus/commit/479f42d2935abe47b4591877080b4a9553e0fd28))

- **board**: Track pricing card hrule alignment in progress
  ([`50e0215`](https://github.com/AnthusAI/Auritus/commit/50e02157966b063b3ab00b02d0e68c98833ba17f))

- **kanbus**: Start auritus-13b752 wire serious voice into cloning models
  ([`a21fd5f`](https://github.com/AnthusAI/Auritus/commit/a21fd5f2fc90b687fe95b5d6bf0633331253fdbd))

### Code Style

- **site**: Align pricing card dividing hrules with css subgrid
  ([#52](https://github.com/AnthusAI/Auritus/pull/52),
  [`58f99ca`](https://github.com/AnthusAI/Auritus/commit/58f99ca56f45e5e744535ae17db74d9a70dca4b0))

### Features

- **scripts**: Add utility to download Steve Jobs reference audio and define voice asset conventions
  ([#53](https://github.com/AnthusAI/Auritus/pull/53),
  [`9e92943`](https://github.com/AnthusAI/Auritus/commit/9e92943147f3d3ab41f2fb19c9daa476e61005c1))

- **tts**: Wire serious voice reference audio into chatterbox, f5, and fish examples
  ([`33bea16`](https://github.com/AnthusAI/Auritus/commit/33bea161c4006bd7be95d6b9c2cf977fff3642cd))


## v0.22.0 (2026-09-18)

### Bug Fixes

- **embed**: Address review feedback on voice selection
  ([#47](https://github.com/AnthusAI/Auritus/pull/47),
  [`8d6cd98`](https://github.com/AnthusAI/Auritus/commit/8d6cd98f7f7fb83b6c1bd4ecd62ee40af1e95257))

- **router**: Respect site-level daily_quota attribute in quota check
  ([`88054f4`](https://github.com/AnthusAI/Auritus/commit/88054f4100a287a6eb36112481a028c400ee7851))

- **worker**: Constrain fish speech max_length to 2048 and load codec on CPU
  ([`c33d8ed`](https://github.com/AnthusAI/Auritus/commit/c33d8ed23d1dc38e479843906b915142bf544bbd))

- **worker**: Ensure fish speech inputs and device match llama model device on cuda
  ([`170dbf9`](https://github.com/AnthusAI/Auritus/commit/170dbf98d2275e193be50c44060ec00c3893229b))

- **worker**: Ensure tensors transfer cleanly between CPU DAC and GPU LLaMA
  ([`0d3c24a`](https://github.com/AnthusAI/Auritus/commit/0d3c24a6d7204b4a6e9b09c13c57dc9d788ac8c6))

- **worker**: Increase fish speech max_length to 8192
  ([`20df406`](https://github.com/AnthusAI/Auritus/commit/20df40625bce900325963c9b9443ac89c790a013))

- **worker**: Keep fish speech DAC vocoder in float32 for audio encoding
  ([`d7094a1`](https://github.com/AnthusAI/Auritus/commit/d7094a13dc350d2602fbab8e01556303c0c8c026))

- **worker**: Offload fish speech DAC vocoder to CPU to eliminate GPU VRAM contention
  ([`08f4737`](https://github.com/AnthusAI/Auritus/commit/08f473741c5a7855971b7bda9c8d47e01e385770))

- **worker**: Optimize fish speech memory allocation and increase batch job memory to 12GB
  ([`bb49f46`](https://github.com/AnthusAI/Auritus/commit/bb49f46c60f7a7ee63c89fbf3f39a95c9fdd35f2))

- **worker**: Optimize fish speech memory with max_length=4096 and cache flushing
  ([`2efa2d4`](https://github.com/AnthusAI/Auritus/commit/2efa2d4d65a3cf6ab57cdf3734d4144b00d47f77))

- **worker**: Remove invalid assignment to DAC.device read-only property
  ([`95aa052`](https://github.com/AnthusAI/Auritus/commit/95aa0520b705c444bc3d4f0a8f8269f76b66fdc1))

- **worker-image**: Bundle basic_ref_en.wav and resolve ref_file safely for F5
  ([`2683c9e`](https://github.com/AnthusAI/Auritus/commit/2683c9e93028aca9f9d8ff9d0dff442ab758f646))

- **worker-image**: Isolate F5-TTS into dedicated venv to resolve Gradio conflict
  ([`a90f6e2`](https://github.com/AnthusAI/Auritus/commit/a90f6e29a7aa08091e562b62efa85af89a50b1a5))

- **worker-image**: Isolate Higgs into dedicated virtualenv with transformers>=5.5.0 for native
  audio tokenizer
  ([`de30261`](https://github.com/AnthusAI/Auritus/commit/de302612346bf7fe26e556243ebd54bef7684ea0))

- **worker-image**: Pre-bake TTS backends into isolated venvs and fix backend APIs
  ([`a23148b`](https://github.com/AnthusAI/Auritus/commit/a23148b7ce7cb975e87613ba4a3ec8c93bf737d4))

### Chores

- Comment on auritus-461f92 with cpu vocoder and tensor bridge fix
  ([`8b1a0a5`](https://github.com/AnthusAI/Auritus/commit/8b1a0a519eb0f7eabf12688b15a398c987b1c565))

- Comment on auritus-461f92 with fish speech vram fix
  ([`df06ac3`](https://github.com/AnthusAI/Auritus/commit/df06ac3fc59e73cf86a936addc0ac33cb1bb3c3d))

- Update kanbus status and comment for auritus-461f92
  ([`bf37377`](https://github.com/AnthusAI/Auritus/commit/bf37377287b36664137b4d82719d031add42936b))

- **board**: Close pitch ignore and flow spacing chores
  ([`a92a798`](https://github.com/AnthusAI/Auritus/commit/a92a7988c9357c813a2a7143d22353cb7be10158))

- **board**: Mark home demo pitch and flow spacing tasks in progress
  ([`aeaa647`](https://github.com/AnthusAI/Auritus/commit/aeaa647a89db28ad06fd7d89a266d7f04a856d34))

- **diagrams**: Update rendered D2 diagrams to match sources
  ([`1e3772f`](https://github.com/AnthusAI/Auritus/commit/1e3772fc864ed25360fd4067e07ff0f415ef7c21))

- **kanbus**: Close auritus-461f92 after verifying fish speech on aws batch
  ([`e89b4d0`](https://github.com/AnthusAI/Auritus/commit/e89b4d0c55104ab4a93187e93f8948a87216b7cd))

- **kanbus**: Commit board state (close auritus-370d16)
  ([`f45ccaa`](https://github.com/AnthusAI/Auritus/commit/f45ccaaed87c9af5964068f0b4502d4518eb8a60))

- **kanbus**: Commit board state (close auritus-a99ed6, track auritus-370d16)
  ([`fc578dd`](https://github.com/AnthusAI/Auritus/commit/fc578ddc9050a6e28a98f3fda4f1b8d020d1b338))

- **kanbus**: Commit board state (issue)
  ([`580560c`](https://github.com/AnthusAI/Auritus/commit/580560ce7d2e65134a39c900a7dfbbb7fcc4503c))

- **kanbus**: Commit board state (issues)
  ([`b89e965`](https://github.com/AnthusAI/Auritus/commit/b89e9658722c905c213d037a251e875c88161c52))

- **kanbus**: Commit board state (issues)
  ([`2be28e4`](https://github.com/AnthusAI/Auritus/commit/2be28e4a2327b97eb359c241c2cbaf3ce42f0931))

- **project**: Track fish speech cuda support task auritus-461f92
  ([`d992e0a`](https://github.com/AnthusAI/Auritus/commit/d992e0a0200ca42c93e016793a864d343ec74e41))

### Code Style

- **site**: Align header nav and cta rightward away from brand lockup
  ([`c5b09ee`](https://github.com/AnthusAI/Auritus/commit/c5b09ee69b024d9abd9b1d63550628004232ac72))

- **site**: Reduce vertical whitespace between header and hero section
  ([`2ba25b3`](https://github.com/AnthusAI/Auritus/commit/2ba25b39907118f3720f476f55e75d6b67121c65))

- **site**: Unify cta buttons with square border radius profile
  ([`61c187e`](https://github.com/AnthusAI/Auritus/commit/61c187ea2b548d52151a625497822fa00ba0935f))

### Features

- **cdk**: Add 100GB gp3 EBS root volume launch template to Batch GPU compute environment
  ([`5731e24`](https://github.com/AnthusAI/Auritus/commit/5731e24121c936e165306ccac890bcec102fc3fe))

- **embed**: Support voice selection and fine-grained voice markup
  ([#47](https://github.com/AnthusAI/Auritus/pull/47),
  [`8d6cd98`](https://github.com/AnthusAI/Auritus/commit/8d6cd98f7f7fb83b6c1bd4ecd62ee40af1e95257))

- **site**: Add delegated responsibility pricing section and page
  ([`14ee91d`](https://github.com/AnthusAI/Auritus/commit/14ee91db10aa5d094b48a73719e7129aab69b7c4))

- **site**: Ignore press play instruction from spoken pitch and add flow section spacing
  ([#51](https://github.com/AnthusAI/Auritus/pull/51),
  [`e3947e4`](https://github.com/AnthusAI/Auritus/commit/e3947e4582145d8804555ffad8ec18b94d1da0ae))

- **worker**: Add native CUDA support for Fish Speech
  ([`47f5023`](https://github.com/AnthusAI/Auritus/commit/47f502363edc1a3b1b74c15565c22961cb1ae3ec))


## v0.21.0 (2026-09-17)


## v0.20.0 (2026-09-17)


## v0.19.0 (2026-09-17)

### Chores

- **kanbus**: Commit board state (comment)
  ([`12b8aa4`](https://github.com/AnthusAI/Auritus/commit/12b8aa43f0a4bd8f44f99a33618f8b23b6132869))

### Features

- **site**: Replace Gettysburg demo with Steve Jobs commencement address and pull quote
  ([`4bcf80d`](https://github.com/AnthusAI/Auritus/commit/4bcf80d8bbe035e2699b7da660a2b680abee2d01))


## v0.18.0 (2026-09-16)

### Bug Fixes

- **admin**: Query per-status GSI partitions for unfiltered job listing
  ([`11ddabc`](https://github.com/AnthusAI/Auritus/commit/11ddabcdc2d5f912be62ae7e6f285f89ae19acf2))

- **cli**: Correct the cost command's empty-result detection
  ([`6f7b201`](https://github.com/AnthusAI/Auritus/commit/6f7b201ab6b59ae8ab3977aa2c10ae19c6266822))

- **cli**: Delegate the Argument make_metavar shim to typer, not click
  ([`764ecdb`](https://github.com/AnthusAI/Auritus/commit/764ecdb5c8a73512273984752133a1430cc9fa9a))

- **cli**: Fix site key lifecycle UX rough edges
  ([`5545b85`](https://github.com/AnthusAI/Auritus/commit/5545b8559e197701651922051041863e2c545d55))

- **console**: Fix a real-environment-only test failure and a race
  ([`e62979d`](https://github.com/AnthusAI/Auritus/commit/e62979d8cc535039711594ded2db83de849f303c))

- **console**: Show real errors on job detail fetch failure
  ([`0550554`](https://github.com/AnthusAI/Auritus/commit/0550554a707242fa4b25585eb1a34165490750ba))

- **console**: Use router.replace for the login redirect
  ([`9a03ebf`](https://github.com/AnthusAI/Auritus/commit/9a03ebf8dbcc267d540a67cc0af8ae50d6df6cf2))

- **router**: Regenerate and retry now clear billing attributes and idempotency flags
  ([`0e1506c`](https://github.com/AnthusAI/Auritus/commit/0e1506c3e3c8d99c282c06e54da31595ba5067e8))

- **router**: Stop mutating tts_backend on content hash collision
  ([`6f8bfa7`](https://github.com/AnthusAI/Auritus/commit/6f8bfa7cb78f8ed80da43a5a6f70f8e48adce2c1))

- **tts**: Load Fish Speech weights with strict=False and accelerate PCM WAV encoding
  ([`3dffbd6`](https://github.com/AnthusAI/Auritus/commit/3dffbd6196cd0e01838c5bcea805f908200d718a))

- **tts**: Properly remap Fish Speech weight keys and enforce strict MLX loading
  ([`1981fca`](https://github.com/AnthusAI/Auritus/commit/1981fca341d28baab83b4776f75d2619da574e2f))

- **worker**: Release claim and mark job failed when TTS generation crashes
  ([`73cf6e6`](https://github.com/AnthusAI/Auritus/commit/73cf6e62b83e1aef87702fe17363bc5537cf73bb))

### Chores

- Exclude console Playwright report/result artifacts from git
  ([`fc876f1`](https://github.com/AnthusAI/Auritus/commit/fc876f12bc4938012804cef4e7f98573d2e11645))

- **kanbus**: Commit board state (issue)
  ([`b271a7e`](https://github.com/AnthusAI/Auritus/commit/b271a7e0284b65f675f50944b6261ec9505a241b))

- **kanbus**: Commit board state (issues)
  ([`f77d90a`](https://github.com/AnthusAI/Auritus/commit/f77d90ae79fbd5851a85d3437b0bb711d264e35c))

- **kanbus**: Commit board state (issues)
  ([`441f6ed`](https://github.com/AnthusAI/Auritus/commit/441f6ed378f5b29e65b9caefdc3c8e13d05bf076))

- **kanbus**: Commit board state (issues)
  ([`0fb4395`](https://github.com/AnthusAI/Auritus/commit/0fb4395b3db490299aa944f2f5d2c45db1349f49))

- **kanbus**: Commit board state (issues)
  ([`01db3f2`](https://github.com/AnthusAI/Auritus/commit/01db3f27b9f843b34457df07dd2ccb616efb001f))

- **kanbus**: Track Fish Speech TTS backend and example page
  ([`18653bf`](https://github.com/AnthusAI/Auritus/commit/18653bf7b29bb80f48b25662e50d0117d6a068a7))

### Code Style

- Run black over new step definitions
  ([`afea69d`](https://github.com/AnthusAI/Auritus/commit/afea69d0f99d7800f1e5b04f57e304a6861fc78e))

- **console**: Use the app's own design tokens on the sites page
  ([`9f6ef73`](https://github.com/AnthusAI/Auritus/commit/9f6ef73a52bff69b2fed99529a8ec1b70e1f739d))

- **console**: Use the danger design token on the costs page error state
  ([`4ab66c7`](https://github.com/AnthusAI/Auritus/commit/4ab66c71ca5c16dbf7f65bf56559a50f8a8aa607))

### Features

- Operator-forced job regeneration with stable content hash
  ([`725d922`](https://github.com/AnthusAI/Auritus/commit/725d922087332b88e7df0f9ccb49b4264b377688))

- **admin**: Add job deletion endpoint and client method
  ([`4d02799`](https://github.com/AnthusAI/Auritus/commit/4d027998275acf7bfc14f8639ec66506fad554ee))

- **admin**: Bulk-delete jobs by site, status, or age
  ([`6f84064`](https://github.com/AnthusAI/Auritus/commit/6f840640445a03e46cc8067d794c1789ad34356e))

- **batch**: Record Batch billed-instance timing on job records
  ([`221c350`](https://github.com/AnthusAI/Auritus/commit/221c3500e56f96e4b34303215f49df3adc22d560))

- **cli**: Add --next-token option to job list command for pagination
  ([`5601aa6`](https://github.com/AnthusAI/Auritus/commit/5601aa66235a0855c94399bd716469f0aaae9bba))

- **cli**: Add cost command for viewing estimated job costs
  ([`9ae9ac6`](https://github.com/AnthusAI/Auritus/commit/9ae9ac69b3e9a5ce789ee598373095a09070fd5c))

- **cli**: Add job command group for list, show, delete, regenerate, retry
  ([`23a2405`](https://github.com/AnthusAI/Auritus/commit/23a2405e7a005aaa22a9aeeacd68e6e48823a28b))

- **console**: Add job management actions to detail page
  ([`b657f9e`](https://github.com/AnthusAI/Auritus/commit/b657f9e996c862c0a64d574dd0e483d611aa89be))

- **console**: Add operator cost visibility in web console
  ([`a18fe88`](https://github.com/AnthusAI/Auritus/commit/a18fe881f7f274b6f451eee7c26d61a94375510e))

- **console**: Add site key management page
  ([`a40a820`](https://github.com/AnthusAI/Auritus/commit/a40a82079ccc37591952af8b9106d8d31afc882a))

- **cost**: Compute avoided cost for local jobs vs Batch fallback
  ([`880c458`](https://github.com/AnthusAI/Auritus/commit/880c458973223f993c27565b09da4f14e1b47af6))

- **cost**: Estimate GPU + platform cost per job from a configurable rate card
  ([`3d0ab89`](https://github.com/AnthusAI/Auritus/commit/3d0ab897fb1f7a8efa8f03004e62e50c3a7e1cbf))

- **cost**: Reconcile estimated GPU cost against the actual AWS bill
  ([`e53f215`](https://github.com/AnthusAI/Auritus/commit/e53f215564d6f35a12b1aae310fb77a8d2f82671))

- **costs**: Roll up job costs daily by site and worker type
  ([`80e4db5`](https://github.com/AnthusAI/Auritus/commit/80e4db5ec6e705bd64091936b0282958be562f59))

- **jobs**: Add retry endpoint for failed and stuck jobs
  ([`1a2faa4`](https://github.com/AnthusAI/Auritus/commit/1a2faa4171ee78a7d2e4ad084d1836efb2baf2b1))

- **retention**: Expire job records and audio on an opt-in retention policy
  ([`3c8b7ee`](https://github.com/AnthusAI/Auritus/commit/3c8b7ee6af8b51eee644fda66dfc80930f2c1184))

- **tts**: Add Fish Speech backend and example comparison page
  ([`ca0fb0d`](https://github.com/AnthusAI/Auritus/commit/ca0fb0daabbdd0b7aab8210f91ac98af21d45db6))

### Testing

- **job-management**: Assert the specific job_not_found error body
  ([`006b31f`](https://github.com/AnthusAI/Auritus/commit/006b31f66b19a61309e7f8f93cd7631abd174bbe))

- **job-regeneration**: Assert against the API response, not the DB key
  ([`dd4ef09`](https://github.com/AnthusAI/Auritus/commit/dd4ef09180d9ec5d8f29b6690adca3e2355673ae))


## v0.17.0 (2026-09-16)


## v0.16.0 (2026-09-15)

### Chores

- **kanbus**: Commit board state (issues)
  ([`c8e5d75`](https://github.com/AnthusAI/Auritus/commit/c8e5d75fb38c0e4434b7aca0b300935c1f3d840e))

- **kanbus**: Commit board state (issues)
  ([`ca5a827`](https://github.com/AnthusAI/Auritus/commit/ca5a827738937a7643d0e7d9813ea6b986dad225))

### Features

- **tts**: Add Higgs Audio v3 backend with MLX and AWS Batch support
  ([`f3495cf`](https://github.com/AnthusAI/Auritus/commit/f3495cf677a717f46ad988b3037087eccf398ee6))


## v0.15.0 (2026-09-15)

### Bug Fixes

- **auth**: Authorize web console client ID on admin routes and display live jobs
  ([`adf8cf5`](https://github.com/AnthusAI/Auritus/commit/adf8cf585820d349f4b45e457c674e24f9fe3d2c))

- **auth**: Enable mutable email attribute for cognito federated sso logins
  ([`edcea21`](https://github.com/AnthusAI/Auritus/commit/edcea217fa6de67886bd767eb4b4dc58aa8f85da))

- **cdk**: Deploy with a current CLI and keep Cognito refresh auth
  ([`7a5c198`](https://github.com/AnthusAI/Auritus/commit/7a5c198c8d97b3c1b9b038b40174ed2220a51f37))

- **cdk**: Do not set ALLOW_REFRESH_TOKEN_AUTH with rotation
  ([`63a2b5d`](https://github.com/AnthusAI/Auritus/commit/63a2b5da0972964f098565c2b826c86f362c7e64))

- **cli**: Bridge click 8.2 make_metavar signature for typer
  ([`e4ec754`](https://github.com/AnthusAI/Auritus/commit/e4ec754e960aeb4a6822e423e6a3d9b2c6b0bb0f))

- **cli**: Bridge click 8.4 UNSET flag_value for typer options
  ([`ecf8436`](https://github.com/AnthusAI/Auritus/commit/ecf843671668e0edd0d48642d14243128954cb1e))

- **console**: Prevent duplicate oauth code exchange flash in callback
  ([`e3c2d6a`](https://github.com/AnthusAI/Auritus/commit/e3c2d6a1184fb27d1003a2d255af5e2c89697559))

- **fallback**: Verify job delivery in step functions with claim grace period
  ([`1264863`](https://github.com/AnthusAI/Auritus/commit/126486335d45f2463464f960f281a8cb94800f77))

### Chores

- **kanbus**: Commit board state (issues)
  ([`dcf3ca3`](https://github.com/AnthusAI/Auritus/commit/dcf3ca3c4eeec6b26642f01cca96194c62f39947))

- **kanbus**: Commit board state (issues)
  ([`00b879b`](https://github.com/AnthusAI/Auritus/commit/00b879b3cabb970795b3a4b7df10635d4a1babf6))

- **kanbus**: Commit board state (issues)
  ([`f0ecfd8`](https://github.com/AnthusAI/Auritus/commit/f0ecfd8feb16f96c0a1f0250c0415285addfcacf))

- **kanbus**: Commit board state (issues)
  ([`4a60500`](https://github.com/AnthusAI/Auritus/commit/4a605004929b657024d0f3bff1ea12721ef8ccd1))

### Code Style

- **site**: Display badge pills on examples index page
  ([`7a3dcf9`](https://github.com/AnthusAI/Auritus/commit/7a3dcf9b44e783c545ae926e74650ee249cc586f))

### Features

- **auth**: Support Google Workspace and AWS IAM Identity Center SSO federation
  ([`cf54cc7`](https://github.com/AnthusAI/Auritus/commit/cf54cc7b80007f6c5038223030aa9b3f4a7b5229))

- **console**: Add cursor-based pagination to admin jobs API and job explorer
  ([`3690f84`](https://github.com/AnthusAI/Auritus/commit/3690f844cc2f44b0da8adb8c8804d0e9746613fe))

- **console**: Wire real Cognito InitiateAuth and add client-side AuthGuard
  ([`e465de1`](https://github.com/AnthusAI/Auritus/commit/e465de1ad0335a7a2f1bb0d7a492aeaafcf9961f))

- **docs**: Add comprehensive google workspace sso guide with exact redirect uris and js origins
  ([`c26ce4c`](https://github.com/AnthusAI/Auritus/commit/c26ce4cb2447c3d8e48fd0798132533d4abee34a))

- **player**: Add play and pause icon toggle with duration and progress display
  ([`be33b4c`](https://github.com/AnthusAI/Auritus/commit/be33b4ceb13abf9461b6a2dfda48f96890451519))

- **site**: Add interactive getting started guide with animated option decision flows
  ([`012e118`](https://github.com/AnthusAI/Auritus/commit/012e118f499f67fd441ec54020cc31f172e2c8a8))

- **site**: Reorganize demo pages into model comparison and embed features
  ([`863d468`](https://github.com/AnthusAI/Auritus/commit/863d4681fe42a3cdb5122cd3665d74aea9660c11))

- **tts**: Add F5-TTS pluggable backend with MLX support
  ([`b5759fe`](https://github.com/AnthusAI/Auritus/commit/b5759fefc1867e6e2a479d1cee82626737ed2abb))

### Testing

- **site**: Prove Play while waiting starts Kokoro speech
  ([`64ba52d`](https://github.com/AnthusAI/Auritus/commit/64ba52d9e12d6391e4cf5dbb15957768fec33f97))


## v0.14.1 (2026-09-14)

### Bug Fixes

- **site**: Stop the wordmark clipping off the top on mobile
  ([`7206550`](https://github.com/AnthusAI/Auritus/commit/7206550fd994f6242ff723fea983d1a192df7d97))


## v0.14.0 (2026-09-13)

### Bug Fixes

- Unbreak Ruff on the operator console telemetry path
  ([`3f7f06c`](https://github.com/AnthusAI/Auritus/commit/3f7f06c125b5b2cb3dcf3aac8a59356bce1fae24))

### Features

- **console**: Operator web console and tts job observability
  ([#40](https://github.com/AnthusAI/Auritus/pull/40),
  [`a082e06`](https://github.com/AnthusAI/Auritus/commit/a082e06e1a971867a36f3299c599439ab0818308))

- **player**: Start speech when Play is pressed while waiting
  ([`cead922`](https://github.com/AnthusAI/Auritus/commit/cead922dd77aeb6378a4f29c1077c4a3cfe493a8))

### Testing

- **site**: Require spoken-length audio on Qwen and example pages
  ([`81fefa2`](https://github.com/AnthusAI/Auritus/commit/81fefa246a455868e97bf4afc4844ed758d66edb))


## v0.13.0 (2026-09-13)

### Features

- **site**: Take the masthead up another step where the room exists
  ([`f7f30fa`](https://github.com/AnthusAI/Auritus/commit/f7f30faab8aff473b8a4191a6b2b3400185565f5))


## v0.12.0 (2026-09-13)

### Features

- **site**: Scale the masthead 1.5x on wide viewports
  ([`6b0ecbf`](https://github.com/AnthusAI/Auritus/commit/6b0ecbf84031ca3abcc819c1596371ce76773ff7))


## v0.11.5 (2026-09-13)

### Bug Fixes

- **site**: Aim the wordmark out of the megaphone
  ([`b871341`](https://github.com/AnthusAI/Auritus/commit/b871341e8460d5c2b4b923bbdae8c88c98c95ce8))


## v0.11.4 (2026-09-13)

### Bug Fixes

- **site**: Danger-red BE HEARD, period on the tagline, smaller headline
  ([`9d62053`](https://github.com/AnthusAI/Auritus/commit/9d62053616596bcd5ac4f7cbbd79d1c5e8f3707c))


## v0.11.3 (2026-09-13)

### Bug Fixes

- **site**: Stop the landing page telling the same story twice
  ([`d6f7390`](https://github.com/AnthusAI/Auritus/commit/d6f73905d632aaa4cdf155fe5143d5e21c232fcb))


## v0.11.2 (2026-09-13)

### Bug Fixes

- **site**: Lead with the audio demo and let the diagrams fill the width
  ([`4071aea`](https://github.com/AnthusAI/Auritus/commit/4071aeaa8c6604683b34dd02d668811788885189))


## v0.11.1 (2026-09-13)

### Bug Fixes

- **site**: Correct the dark diagram canvas and make the hero diagram readable
  ([`fb2be1c`](https://github.com/AnthusAI/Auritus/commit/fb2be1ce275bc795c9d2abfe9f16c0c4c9a41bd6))

### Continuous Integration

- Run Behave and Playwright on develop
  ([`a455a2d`](https://github.com/AnthusAI/Auritus/commit/a455a2d51818ec72c77fbb85615b9ee38917c4a3))

- Set AWS region so Behave can import the router handler
  ([`cb8660f`](https://github.com/AnthusAI/Auritus/commit/cb8660f6276592b3cd47d5756b3993efc502f163))

### Documentation

- **site**: Explain the no-IAM-key auth architecture with diagrams
  ([`9f4225a`](https://github.com/AnthusAI/Auritus/commit/9f4225a10814a867a7745f551f92c7518e762e49))

### Testing

- **site**: Follow the rewritten security page
  ([`331c366`](https://github.com/AnthusAI/Auritus/commit/331c3666802e6e3f26d6b87c8f067d04a17a745a))

- **site**: Require spoken-length audio on the home pitch
  ([`e0addbc`](https://github.com/AnthusAI/Auritus/commit/e0addbc4a57a2157adefbf3ed2c616175f90b9f6))


## v0.11.0 (2026-09-13)

### Build System

- Make diagram renders reproducible and builds dev-safe
  ([`34d3775`](https://github.com/AnthusAI/Auritus/commit/34d377536297d57c630002f65ccff68268f7efd2))

### Code Style

- **site**: Format ElevatorPitch with Prettier
  ([`2e8ee7a`](https://github.com/AnthusAI/Auritus/commit/2e8ee7abc634c60a1d303d7472575753fcfec038))

### Documentation

- Render diagrams in the newsprint palette
  ([`20f149e`](https://github.com/AnthusAI/Auritus/commit/20f149ea8bfbf783b47ae7ac22afa68888076eb3))

### Features

- Speak the home-page pitch and stop overlapping boots from wiping the player
  ([`dfb3b11`](https://github.com/AnthusAI/Auritus/commit/dfb3b1100cabb41539472d61c938fb672dd09d28))


## v0.10.0 (2026-09-13)

### Bug Fixes

- **auth**: Isolate alert rate-limit keys in a dedicated table
  ([`7c2713d`](https://github.com/AnthusAI/Auritus/commit/7c2713d1d5f350c4d48b345fd374128709eaeac6))

### Chores

- Record shipped TTS licenses and skip PyPI until enabled
  ([`86ee30d`](https://github.com/AnthusAI/Auritus/commit/86ee30d4cb71070bb44461713193a3a959494428))

### Features

- **auth**: Unattended worker auth via refresh-token rotation
  ([`1ba9c01`](https://github.com/AnthusAI/Auritus/commit/1ba9c017cb8fe3453b5096032f80dca935e4c8cf))


## v0.9.0 (2026-09-13)

### Documentation

- Add visual architecture and landing page
  ([`48d8228`](https://github.com/AnthusAI/Auritus/commit/48d822862c5f3b44777d25b0e74b4af557bb06ca))

- Clarify local workers race Batch after the claim timeout
  ([`238f7d6`](https://github.com/AnthusAI/Auritus/commit/238f7d66249935de6997b82dc3d53730df597a1a))

### Features

- Show Play chrome before boot and restart finished clips
  ([`a8ffbac`](https://github.com/AnthusAI/Auritus/commit/a8ffbac3e547072d2059e0955cada443a8e2c8e0))


## v0.8.0 (2026-09-13)

### Bug Fixes

- Use Qwen3TTSModel on Linux Batch and pin torchaudio
  ([`5665f99`](https://github.com/AnthusAI/Auritus/commit/5665f9958397e0830d27cec3e616c12faeefaa3a))

### Documentation

- Name Kokoro and Qwen as speech backends in the README
  ([`22c2296`](https://github.com/AnthusAI/Auritus/commit/22c2296db690d22e64f36daf4c88ee57a4ca834b))

### Features

- Bake Qwen into the Batch worker image
  ([`97b81a0`](https://github.com/AnthusAI/Auritus/commit/97b81a027331116e4fff9eb5c4c2d642de046bb7))


## v0.7.0 (2026-09-13)

### Features

- Speak the same Gettysburg excerpt through Kokoro and Qwen
  ([`52f61de`](https://github.com/AnthusAI/Auritus/commit/52f61de2b1d3b9b73c51edab7adaffe5f58efb6d))


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
