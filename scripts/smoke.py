#!/usr/bin/env python3
"""Smoke test for Vibe-Trading (HKUDS/Vibe-Trading).

Imports the installed package, prints its version, runs its CLI with
--help via subprocess, and writes:
  - results/smoke.json  {ok, package, version, cli_help_ok}
  - results/smoke.md    with the quoted CLI help output (first ~40 lines)

The installed PyPI distribution is ``vibe-trading-ai`` (per the upstream
pyproject.toml / README Quick Start: ``pip install vibe-trading-ai``);
its top-level import package is ``cli`` and its console script is
``vibe-trading`` (``vibe-trading = "cli:main"``). No LLM key is needed
for this smoke test and no real analysis is run.
"""

import importlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

RESULTS = Path("results")
RESULTS.mkdir(parents=True, exist_ok=True)

PACKAGE = "vibe-trading-ai"


def get_version() -> str:
    try:
        return importlib.metadata.version(PACKAGE)
    except Exception:
        pass
    try:
        from cli._version import __version__

        return str(__version__)
    except Exception:
        return "unknown"


def main() -> int:
    version = get_version()
    print(f"package: {PACKAGE}")
    print(f"version: {version}")

    import_ok = False
    for mod_name in ("cli", "src"):
        try:
            importlib.import_module(mod_name)
            import_ok = True
            print(f"import {mod_name}: ok")
            break
        except Exception as exc:  # noqa: BLE001 - smoke test reports any failure
            print(f"import {mod_name}: FAILED {type(exc).__name__}: {exc}")

    cli_help_lines = []
    cli_help_ok = False
    exe = shutil.which("vibe-trading")
    print(f"vibe-trading executable: {exe}")
    if exe:
        try:
            proc = subprocess.run(
                [exe, "--help"],
                capture_output=True,
                text=True,
                timeout=120,
                stdin=subprocess.DEVNULL,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            cli_help_lines = out.splitlines()
            print(f"vibe-trading --help exit code: {proc.returncode}")
            cli_help_ok = proc.returncode == 0 and len(cli_help_lines) > 0
        except Exception as exc:  # noqa: BLE001
            cli_help_lines = [
                f"ERROR running vibe-trading --help: {type(exc).__name__}: {exc}"
            ]
            print(cli_help_lines[0])
    else:
        cli_help_lines = ["ERROR: vibe-trading executable not found on PATH"]
        print(cli_help_lines[0])

    first40 = cli_help_lines[:40]
    print("--- vibe-trading --help (first ~40 lines) ---")
    for line in first40:
        print(line)
    print("--- end of help excerpt ---")

    ok = bool(import_ok and version != "unknown" and cli_help_ok)
    data = {
        "ok": ok,
        "package": PACKAGE,
        "version": version,
        "cli_help_ok": cli_help_ok,
    }
    (RESULTS / "smoke.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Vibe-Trading smoke test",
        "",
        f"- Package: `{PACKAGE}`",
        f"- Version: `{version}`",
        f"- Import ok: `{import_ok}`",
        f"- CLI help ok: `{cli_help_ok}`",
        f"- OK: `{ok}`",
        "",
        "## `vibe-trading --help` (first ~40 lines)",
        "",
        "```text",
        *first40,
        "```",
        "",
    ]
    (RESULTS / "smoke.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(json.dumps(data, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
