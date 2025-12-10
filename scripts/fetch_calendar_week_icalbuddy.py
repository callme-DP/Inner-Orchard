#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用 icalBuddy 读取指定周（默认本周）的日历事件，输出 JSON。
- 依赖：icalBuddy（可通过 brew install ical-buddy 安装）
- 输出：data/calendar/week-<ISO周>-icalbuddy.json
- 字段：title, calendar, start, end, allday, location, notes
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "data" / "calendar"


def iso_week_str(d: date) -> str:
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def run_icalbuddy(start_day: date, end_day: date, calendars: List[str] | None) -> List[Dict[str, Any]]:
    if not shutil.which("icalBuddy"):
        raise RuntimeError("未找到 icalBuddy，请先安装（brew install ical-buddy）")

    # 输出属性顺序：title, calendarName, allDayEvent, datetime, location, notes
    props = "title,calendarName,allDayEvent,datetime,location,notes"
    cmd = [
        "icalBuddy",
        "-b",
        "",
        "--dateFormat",
        "%Y-%m-%d",
        "--timeFormat",
        "%H:%M",
        "-po",
        props,
        "-ps",
        "|@|",
        f"eventsFrom:{start_day.isoformat()}",
        f"to:{end_day.isoformat()}",
    ]
    if calendars:
        cmd[1:1] = ["-ic", ",".join(calendars)]

    output = subprocess.check_output(cmd, text=True)
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    events: List[Dict[str, Any]] = []
    for line in lines:
        parts = line.split("|@|")
        if len(parts) < 6:
            continue
        title, cal_name, allday, dt_field, location, notes = parts[:6]
        start_iso, end_iso, allday_bool = parse_datetime(dt_field, allday.lower() == "yes")
        events.append(
            {
                "title": title,
                "calendar": cal_name,
                "start": start_iso,
                "end": end_iso,
                "allday": allday_bool,
                "location": location,
                "notes": notes,
            }
        )
    return events


def parse_datetime(dt_field: str, allday_flag: bool):
    """
    将形如 '2024-12-09 09:30 - 12:00' 或 '2024-12-09' 转为 ISO。
    """
    tz = datetime.now().astimezone().tzinfo
    if " - " in dt_field:
        date_part, times = dt_field.split(" ", 1)
        start_time, end_time = times.split(" - ")
        start_dt = datetime.fromisoformat(f"{date_part} {start_time}:00").replace(tzinfo=tz)
        end_dt = datetime.fromisoformat(f"{date_part} {end_time}:00").replace(tzinfo=tz)
        return start_dt.isoformat(), end_dt.isoformat(), allday_flag
    else:
        day = dt_field.strip()
        start_dt = datetime.fromisoformat(f"{day} 00:00:00").replace(tzinfo=tz)
        end_dt = datetime.fromisoformat(f"{day} 23:59:59").replace(tzinfo=tz)
        return start_dt.isoformat(), end_dt.isoformat(), True


def main() -> int:
    parser = argparse.ArgumentParser(description="用 icalBuddy 抓取一周内的日历事件")
    parser.add_argument("--start", help="周起始日期 YYYY-MM-DD（默认本周周一）")
    parser.add_argument("--cals", help="限定日历名称，逗号分隔（可选）")
    args = parser.parse_args()

    today = date.today()
    start_day = date.fromisoformat(args.start) if args.start else (today - timedelta(days=today.weekday()))
    end_day = start_day + timedelta(days=7)
    cal_list = [c.strip() for c in args.cals.split(",")] if args.cals else None

    events = run_icalbuddy(start_day, end_day, cal_list)
    payload = {
        "week": iso_week_str(start_day),
        "start": start_day.isoformat(),
        "end": end_day.isoformat(),
        "events": events,
        "count": len(events),
        "source": "icalBuddy",
        "calendars": cal_list or "all",
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"week-{iso_week_str(start_day)}-icalbuddy.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写入完成：{out_path}（{len(events)} 条事件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
