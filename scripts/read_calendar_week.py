#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取 `scripts/fetch_calendar.py` 生成的周级日历 JSON，转换为渲染需要的日/周结构。
输出结构参考 specs/time-energy-visualization/mock-data/calendar.mock.json 的 day/week。
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data" / "calendar"


def iso_week_str(d: date) -> str:
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def parse_week(value: str) -> str:
    """Validate week string like 2025-W50."""
    try:
        year_part, week_part = value.split("-W")
        date.fromisocalendar(int(year_part), int(week_part), 1)
    except Exception as exc:
        raise argparse.ArgumentTypeError("week must be like 2025-W50") from exc
    return value


def week_start_from_label(label: str) -> date:
    year_part, week_part = label.split("-W")
    return date.fromisocalendar(int(year_part), int(week_part), 1)


def find_source_path(week_label: str, explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"指定的输入不存在：{path}")
        return path

    candidates = [
        DATA_DIR / f"week-{week_label}.json",
        DATA_DIR / f"week-{week_label}-icalbuddy.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"未找到日历源文件：{', '.join(str(c) for c in candidates)}")


def load_events(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    events = data.get("events") or []
    return [evt for evt in events if isinstance(evt, dict)]


def normalize_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for evt in events:
        start_raw = evt.get("start")
        end_raw = evt.get("end")
        if not start_raw or not end_raw:
            continue
        try:
            start_dt = datetime.fromisoformat(str(start_raw))
            end_dt = datetime.fromisoformat(str(end_raw))
        except ValueError:
            continue
        duration_min = max(0, int((end_dt - start_dt).total_seconds() // 60))
        normalized.append(
            {
                "date": start_dt.date().isoformat(),
                "start": start_dt.strftime("%H:%M"),
                "end": end_dt.strftime("%H:%M"),
                "title": evt.get("title") or "",
                "calendar": evt.get("calendar") or "",
                "category": evt.get("category") or evt.get("calendar") or "",
                "duration_minutes": duration_min,
                "notes": evt.get("notes") or "",
            }
        )
    normalized.sort(key=lambda x: (x["date"], x["start"], x["title"]))
    return normalized


def build_payload(week_label: str, day_label: str | None, events: List[Dict[str, Any]], source_path: Path) -> Dict[str, Any]:
    day_for_view = day_label or (week_start_from_label(week_label).isoformat() if events else None)
    day_rows = [evt for evt in events if evt["date"] == day_for_view] if day_for_view else []
    return {
        "periods": ["day", "week"],
        "day": day_rows,
        "week": events,
        "meta": {
            "week": week_label,
            "selected_day": day_for_view,
            "source": str(source_path),
            "event_count": len(events),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="读取周级日历 JSON 并输出 day/week 结构")
    parser.add_argument("--week", default=None, type=parse_week, help="周标签，如 2025-W50（默认当前周）")
    parser.add_argument("--day", help="day 视图展示的日期，YYYY-MM-DD，可选")
    parser.add_argument("--input", help="源文件路径，默认 data/calendar/week-<week>.json 或 -icalbuddy 版本")
    parser.add_argument("--output", help="输出路径，默认 data/calendar/normalized-week-<week>.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    today = date.today()
    week_label = args.week or iso_week_str(today - timedelta(days=today.weekday()))
    source_path = find_source_path(week_label, args.input)
    events = normalize_events(load_events(source_path))
    payload = build_payload(week_label, args.day, events, source_path)
    out_path = Path(args.output) if args.output else DATA_DIR / f"normalized-week-{week_label}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写入完成：{out_path}，事件数：{len(events)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
