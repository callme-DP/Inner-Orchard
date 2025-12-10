#!/usr/bin/env python3
"""
Append a mood/energy entry to a local JSONL file.
Fields are compatible with a simple daily schema: day, slot (morning/noon/evening), score, tags, notes.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a mood/energy record to data/mood/log.jsonl")
    parser.add_argument("--day", default=str(date.today()), help="Day YYYY-MM-DD (default: today)")
    parser.add_argument("--slot", choices=["morning", "noon", "evening"], required=True, help="Day slot")
    parser.add_argument("--score", type=float, required=True, help="Score 1-10")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--notes", default="", help="Free-form notes")
    parser.add_argument("--output", default="data/mood/log.jsonl", help="Output JSONL path (git-ignored)")
    return parser.parse_args()


def ensure_range(score: float) -> float:
    return max(1.0, min(10.0, score))


def main() -> int:
    args = parse_args()
    record = {
        "day": args.day,
        "slot": args.slot,
        "score": ensure_range(args.score),
        "tags": [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else [],
        "notes": args.notes,
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Appended mood record to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
