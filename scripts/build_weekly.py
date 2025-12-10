#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 weekly HTML：
- 读取本地日历 JSON（data/calendar/week-*.json），若不存在则用 mock。
- 读取 mock 的 ActivityWatch/Mood/Incidents。
- 将数据注入 html/v1/weekly_mock.html，输出 html/output/weekly.html。
"""

from __future__ import annotations

import argparse
import glob
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

BASE = Path(__file__).resolve().parent.parent
CAL_DIR = BASE / "data" / "calendar"
MOCK_DIR = BASE / "specs" / "time-energy-visualization" / "mock-data"
TEMPLATE = BASE / "html" / "v1" / "weekly_mock.html"
OUT_HTML = BASE / "html" / "output" / "weekly.html"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_calendar(path_arg: str | None) -> Path | None:
    if path_arg:
        p = Path(path_arg)
        return p if p.exists() else None
    candidates = sorted(glob.glob(str(CAL_DIR / "week-*.json")), key=lambda p: Path(p).stat().st_mtime, reverse=True)
    return Path(candidates[0]) if candidates else None


def normalize_calendar(cal_data: Dict[str, Any]) -> Dict[str, Any]:
    events = cal_data.get("events") or []
    norm: List[Dict[str, Any]] = []
    category_totals: Dict[str, int] = {}
    notes_count = 0
    for evt in events:
        try:
            start_dt = datetime.fromisoformat(evt["start"])
            end_dt = datetime.fromisoformat(evt["end"])
        except Exception:
            continue
        duration_minutes = max(0, int((end_dt - start_dt).total_seconds() // 60))
        calendar_name = evt.get("calendar") or "未分类"
        if evt.get("notes"):
            notes_count += 1
        category_totals[calendar_name] = category_totals.get(calendar_name, 0) + duration_minutes
        norm.append(
            {
                "date": start_dt.date().isoformat(),
                "start": start_dt.strftime("%H:%M"),
                "end": end_dt.strftime("%H:%M"),
                "title": evt.get("title", ""),
                "category": calendar_name,
                "calendar": calendar_name,
                "duration_minutes": duration_minutes,
                "notes": evt.get("notes", ""),
            }
        )
    # 按日期倒序、时间升序排序
    norm.sort(key=lambda x: (x["date"], x["start"]), reverse=True)
    return {
        "week": norm,
        "month": [],
        "year": [],
        "category_totals": category_totals,
        "notes_count": notes_count,
    }


def build_payload(calendar_path: Path | None) -> Dict[str, Any]:
    # 活动/情绪/突发任务使用 mock
    aw = load_json(MOCK_DIR / "activitywatch.aggregate.json")
    mood = load_json(MOCK_DIR / "mood.week.json")
    incidents = load_json(MOCK_DIR / "incidents.week.json")

    if calendar_path and calendar_path.exists():
        cal_raw = load_json(calendar_path)
    else:
        cal_raw = load_json(MOCK_DIR / "calendar.mock.json")
    cal_norm = normalize_calendar(cal_raw)

    # 用日历类别时长覆盖左侧类别卡片（上一周期为空，使用占位）
    aw_from_cal = []
    for name, minutes in cal_norm.get("category_totals", {}).items():
        aw_from_cal.append(
            {
                "name": name,
                "duration_minutes": minutes,
                "baseline_minutes": 0,
                "change_pct": None,
            }
        )
    if aw_from_cal:
        aw_payload = {
            "day": aw_from_cal,
            "week": aw_from_cal,
            "month": aw_from_cal,
            "year": aw_from_cal,
        }
    else:
        aw_payload = aw

    return {
        "periods": ["week", "month", "year"],
        "activitywatch": aw_payload,
        "mood": mood,
        "incidents": incidents,
        "calendar": cal_norm,
        "meta": {
            "calendar_source": str(calendar_path) if calendar_path else "mock",
            "notes_count": cal_norm.get("notes_count", 0),
        },
    }


def inject_html(payload: Dict[str, Any]) -> None:
    raw_html = TEMPLATE.read_text(encoding="utf-8")
    html = raw_html.replace("__MOCK_DATA__", json.dumps(payload, ensure_ascii=False, indent=2))
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="生成 weekly 仪表盘 HTML")
    p.add_argument("--calendar", help="指定日历 JSON 路径，默认选择 data/calendar 中最新的 week-*.json")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cal_path = find_calendar(args.calendar)
    payload = build_payload(cal_path)
    inject_html(payload)
    print(f"生成完成：{OUT_HTML}（日历源：{payload['meta']['calendar_source']}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
