#!/usr/bin/env python3
"""Restore four genuine archived Git commits locally; never manufacture history."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
TARGET = "refs/heads/archive/original-L1-L2"
EXPECTED = "3afb63d39d2dd5ee359141756d59bd0daa100684"


def main():
    bundle = ROOT / "history" / "original_L1_L2.bundle"
    subprocess.run(["git", "-C", str(ROOT), "bundle", "verify", str(bundle)], check=True)
    existing = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", TARGET], capture_output=True, text=True)
    if existing.returncode == 0:
        if existing.stdout.strip() != EXPECTED:
            raise RuntimeError("Recovery branch exists at another commit; refusing to overwrite it.")
        print("The original history is already restored.")
        return
    subprocess.run(["git", "-C", str(ROOT), "fetch", str(bundle), f"refs/heads/master:{TARGET}"], check=True)
    subprocess.run(["git", "-C", str(ROOT), "log", "--format=%H %aI %s", TARGET], check=True)
    print("Restored only the four commits in the original project archive. No network push, backdating or new historical claim was made.")


if __name__ == "__main__":
    main()

