#!/usr/bin/env python
import os
import shutil
import subprocess
import sys
from pathlib import Path


def candidate_env_roots():
    seen = set()
    for value in (os.environ.get("CONDA_PREFIX"), sys.prefix, sys.base_prefix):
        if not value:
            continue
        root = Path(value).resolve()
        if root not in seen:
            seen.add(root)
            yield root


def rscript_path():
    names = ["Rscript.exe", "Rscript"] if os.name == "nt" else ["Rscript", "Rscript.exe"]
    for root in candidate_env_roots():
        for name in names:
            candidate = root / ("Scripts" if os.name == "nt" else "bin") / name
            if candidate.exists():
                return str(candidate)
            candidate = root / "Lib" / "R" / "bin" / name
            if candidate.exists():
                return str(candidate)
    resolved = shutil.which("Rscript")
    if resolved:
        return resolved
    raise SystemExit("Unable to locate Rscript in CONDA_PREFIX, Python prefix, or PATH")


def r_dll_paths():
    paths = []
    if os.name != "nt":
        return paths
    for root in candidate_env_roots():
        for relative in (
            Path("Library") / "bin",
            Path("Lib") / "R" / "bin",
            Path("Scripts"),
        ):
            candidate = root / relative
            if candidate.exists():
                paths.append(str(candidate))
    return paths


def main(argv):
    if not argv:
        raise SystemExit("Usage: run_rscript.py <script.R> [args...]")
    env = os.environ.copy()
    dll_paths = r_dll_paths()
    if dll_paths:
        env["PATH"] = os.pathsep.join([*dll_paths, env.get("PATH", "")])
    command = [rscript_path(), *argv]
    completed = subprocess.run(command, env=env, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
