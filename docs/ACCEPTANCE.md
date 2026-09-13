# Acceptance tests

The example pages under `site/app/examples/` are the acceptance fixtures:

- `/examples/basic` — end-to-end generation + play
- `/examples/ignore-rules` — CSS + data-auritus-ignore + pronounce
- `/examples/themed` — CSS custom-property theming

Run against a deployed API + local worker:

```bash
auritus login --username you@example.com
auritus worker
# open https://aurit.us/examples/basic
```
