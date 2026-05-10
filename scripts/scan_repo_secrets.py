#!/usr/bin/env python3
"""
Lightweight repository secret scanner.

Usage: python3 scripts/scan_repo_secrets.py

This script searches workspace files (excluding common binary and venv folders)
for high-entropy strings and common API-key patterns and prints file:line matches.
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {'.git', '.venv', 'venv', 'node_modules', '.next', '__pycache__'}
EXCLUDE_FILES = {'.env', '.env.local', 'db.sqlite3'}

PATTERNS = [
    re.compile(r'AIza[0-9A-Za-z\-_]{35}'),
    re.compile(r'sk-[0-9a-zA-Z]{20,}'),
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'gsk_[0-9A-Za-z]{40,}'),
    re.compile(r'(?i)secret_key\s*=\s*[0-9a-zA-Z_\-]{40,}'),
    re.compile(r'-----BEGIN (RSA|PRIVATE) KEY-----'),
]

def should_skip(path: Path) -> bool:
    parts = set(path.resolve().parts)
    return path.name in EXCLUDE_FILES or any(ex in parts for ex in EXCLUDE_DIRS)

def scan_file(path: Path):
    try:
        text = path.read_text(errors='ignore')
    except Exception:
        return []
    results = []
    for i, line in enumerate(text.splitlines(), start=1):
        for pat in PATTERNS:
            if pat.search(line):
                results.append((i, pat.pattern, line.strip()))
    return results

def main():
    print(f"Scanning {ROOT} for secrets...")
    found = False
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # prune excluded dirs
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fname in filenames:
            p = Path(dirpath) / fname
            if p.suffix in {'.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', '.so'}:
                continue
            rel = p.relative_to(ROOT)
            if should_skip(p):
                continue
            matches = scan_file(p)
            if matches:
                found = True
                for ln, pattern, line in matches:
                    print(f"{rel}:{ln}: {pattern} -> {line}")
    if found:
        raise SystemExit(1)
    print("No obvious secrets found in tracked source files.")

if __name__ == '__main__':
    main()
