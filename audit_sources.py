#!/usr/bin/env python3
"""Source audit for Axezent AI PRK-Fuzzer launch-safe claim discipline."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
BLOCKED_PHRASES = [
    "proves p=np",
    "solves p=np",
    "proves rh",
    "trillion-dollar guaranteed",
    "guarantees fame",
    "proves global solver correctness",
]
SKIP_DIRS = {".git", ".github", "target", "__pycache__", ".pytest_cache", "generated_batch"}
EXTS = {".md", ".py", ".json", ".toml", ".rs", ".yml", ".yaml", ".cff"}


def main() -> int:
    errors: list[str] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name == "audit_sources.py":
            continue
        if not path.is_file() or path.suffix not in EXTS:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in BLOCKED_PHRASES:
            if phrase in text:
                errors.append(f"{path.relative_to(ROOT)} contains blocked phrase: {phrase}")
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1
    print("Axezent AI PRK-Fuzzer source audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
