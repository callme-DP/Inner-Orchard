#!/usr/bin/env python3
"""
Pull ActivityWatch aw-watcher-web events for a given date and write a simple aggregate.
- Defaults to local API at http://localhost:5600/api/0
- Looks for buckets containing "aw-watcher-web"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen


def iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_json(url: str) -> Any:
    with urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def list_buckets(base_url: str) -> List[str]:
    buckets_url = f"{base_url}/buckets"
    data = fetch_json(buckets_url)
    return [entry["id"] for entry in data]


def fetch_events(base_url: str, bucket_id: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
    params = urlencode({"start": iso_utc(start), "end": iso_utc(end)})
    url = f"{base_url}/buckets/{bucket_id}/events?{params}"
    events = fetch_json(url)
    return events


def aggregate(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_seconds = 0.0
    per_title: Dict[str, float] = {}
    for evt in events:
        duration = float(evt.get("duration", 0.0))
        data = evt.get("data", {}) or {}
        title = data.get("title") or data.get("url") or "unknown"
        total_seconds += duration
        per_title[title] = per_title.get(title, 0.0) + duration
    return {
        "total_seconds": total_seconds,
        "by_title_seconds": per_title,
        "event_count": len(events),
    }


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch ActivityWatch web watcher events for a date.")
    parser.add_argument("--date", dest="day", default=str(date.today()), help="Date YYYY-MM-DD (default: today)")
    parser.add_argument("--base-url", default=os.environ.get("AW_URL", "http://localhost:5600/api/0"), help="ActivityWatch API base")
    parser.add_argument("--output", help="Output path (default: data/activitywatch/<date>.json)")
    parser.add_argument("--bucket-substring", default="aw-watcher-web", help="Bucket id substring to match")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        target_day = date.fromisoformat(args.day)
    except ValueError:
        print("Invalid --date, expected YYYY-MM-DD", file=sys.stderr)
        return 1

    start_dt = datetime.combine(target_day, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    output_path = Path(args.output) if args.output else Path("data/activitywatch") / f"{args.day}.json"

    try:
        buckets = list_buckets(args.base_url)
    except (URLError, HTTPError) as exc:
        print(f"Failed to list buckets from {args.base_url}: {exc}", file=sys.stderr)
        return 1

    buckets = [b for b in buckets if args.bucket_substring in b]
    if not buckets:
        print(f"No buckets matched '{args.bucket_substring}'", file=sys.stderr)
        return 1

    results = []
    for bucket_id in buckets:
        try:
            events = fetch_events(args.base_url, bucket_id, start_dt, end_dt)
        except (URLError, HTTPError) as exc:
            print(f"Failed to fetch events for {bucket_id}: {exc}", file=sys.stderr)
            continue
        results.append({"bucket": bucket_id, "aggregate": aggregate(events), "events": events})

    payload = {
        "source": "activitywatch",
        "base_url": args.base_url,
        "date": args.day,
        "buckets": results,
        "generated_at": iso_utc(datetime.now(timezone.utc)),
    }

    save_json(output_path, payload)
    print(f"Wrote {output_path} with {len(results)} bucket(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
