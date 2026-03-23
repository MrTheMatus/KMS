"""Optional helper to pull Ollama models (Etap 1/3 local-first).

This control-plane repo intentionally does not depend on Ollama at runtime.
The script exists only to help with local-first setup.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess


def _parse_models_arg(models_arg: str | None) -> list[str]:
    if not models_arg:
        return []
    parts = [p.strip() for p in models_arg.split(",")]
    return [p for p in parts if p]


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull Ollama models (optional helper).")
    parser.add_argument(
        "--models",
        default=None,
        help="Comma-separated list of Ollama models to pull. "
        "If omitted, uses OLLAMA_MODELS env var.",
    )
    args = parser.parse_args()

    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        print("ollama is not installed (command not found).", flush=True)
        return 1

    models = _parse_models_arg(args.models) or _parse_models_arg(os.environ.get("OLLAMA_MODELS"))
    if not models:
        print("No models specified. Provide --models or set OLLAMA_MODELS.", flush=True)
        return 2

    ok = True
    for model in models:
        print(f"Pulling model: {model}", flush=True)
        proc = subprocess.run(["ollama", "pull", model], check=False, text=True)
        if proc.returncode != 0:
            ok = False
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())

