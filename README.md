# vibe-trading-runner

Runs [Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) (HKUDS) analyses on
GitHub Actions, where the commands to execute live in a repository **Actions
variable** — not in code.

> **Smoke-only for now.** This repo is set up and verified with a smoke test
> only. No real analysis run has been attempted. Real runs await the
> `GOOGLE_API_KEY` and `GROQ_API_KEY` repository secrets (LLM keys are being
> provisioned separately).

## The pattern (one repo per tool)

1. **Edit the commands**: repo *Settings → Secrets and variables → Actions →
   Variables* → set the `COMMANDS` variable to whatever shell commands this
   run should execute (multi-line works). The same can be done through the
   GitHub API (`POST /repos/{owner}/{repo}/actions/variables` to create, or
   `PUT /repos/{owner}/{repo}/actions/variables/COMMANDS` to update).
2. **Trigger manually**: *Actions* tab → “Run analysis” → *Run workflow*
   (or `POST /repos/{owner}/{repo}/actions/workflows/run.yml/dispatches`).
   The workflow has **no other triggers** — it runs only when dispatched
   (`workflow_dispatch` only).
3. **Collect results**: the workflow uploads everything under `results/` as
   the `results` build artifact (`if: always()`, so partial results survive
   a failing step). Download it from the run page or via the API.

The workflow itself is generic: checkout → Python 3.11
(`actions/setup-python@v5`) → `pip install -r requirements.txt` → run
`${{ vars.COMMANDS }}` → upload `results/` (`actions/upload-artifact@v4`).
To run a different analysis, change the variable — not the workflow.

The “Run commands” step carries these environment variables for future
real runs (secrets are read at run time; nothing is stored in code):

```yaml
env:
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
```

## Tool: Vibe-Trading

- Upstream: https://github.com/HKUDS/Vibe-Trading — “Vibe-Trading: Your
  Personal Trading Agent”, a natural-language finance research AI agent
  with backtesting.
- Install (per the upstream README): `pip install vibe-trading-ai` from
  PyPI, or from the GitHub repo as in this repo’s `requirements.txt`:

  ```
  git+https://github.com/HKUDS/Vibe-Trading
  ```

  The PyPI distribution name is `vibe-trading-ai`; once installed it
  provides the `vibe-trading` CLI (and `vibe-trading-mcp`).
- Python 3.11+ is required upstream; this runner uses Python 3.11.

## Current (smoke) `COMMANDS` value

```sh
mkdir -p results
set -o pipefail; python scripts/smoke.py 2>&1 | tee results/run.log
```

`scripts/smoke.py` imports the installed package (`vibe-trading-ai`,
top-level import package `cli`), prints its version (or `unknown` if it
exposes none), runs `vibe-trading --help` via subprocess and saves the
first ~40 lines, and writes:

- `results/smoke.json` — `{ok, package, version, cli_help_ok}`
- `results/smoke.md` — the smoke summary with the quoted CLI help output
- `results/run.log` — the full step log (via `tee`)

The `set -o pipefail;` prefix matters: piping through `tee` would
otherwise mask a script failure and make a failed run show as “success”.

## How to trigger a real run later

1. Add the LLM secrets: repo *Settings → Secrets and variables → Actions →
   Secrets* → `GOOGLE_API_KEY` and/or `GROQ_API_KEY` (whichever provider
   the run will use). Real runs do not start until these secrets exist.
2. Change the `COMMANDS` Actions variable from the smoke command above to
   the real Vibe-Trading command(s) for the analysis — always keeping
   line 1 as `mkdir -p results` and prefixing the run line with
   `set -o pipefail;` and piping it `2>&1 | tee results/run.log`, so the
   log and any files written under `results/` are collected as the
   `results` artifact even on failure.
3. Dispatch the workflow (Actions tab → “Run analysis” → *Run workflow*,
   or the dispatches API above) and download the `results` artifact from
   the finished run.

Nothing in the workflow or the runner pattern is tied to one exchange:
scripts take the ticker symbol and analysis parameters as inputs, so the
same repo can analyse an EGX stock today and a US stock tomorrow — only
the inputs in `COMMANDS` change.
