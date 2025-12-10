#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 icalBuddy 读取指定周（默认本周）的日历事件。
- 原始输出：data/calendar/raw/week-<ISO周>.txt
- 解析输出：data/calendar/week-<ISO周>.json
- 日志：data/calendar/fetch_calendar.log（每次运行重置）
支持 yesterday/today/绝对日期；支持 sample-day 小范围验证。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "data" / "calendar"
RAW_DIR = OUT_DIR / "raw"
LOG_FILE = OUT_DIR / "fetch_calendar.log"


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text((LOG_FILE.read_text() if LOG_FILE.exists() else "") + msg + "\n", encoding="utf-8")


def iso_week_str(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def run_icalbuddy(start_day: date, end_day: date) -> List[str]:
    # 使用带属性输出的单行模式，便于解析
    cmd = [
        "icalBuddy",
        "-npn",
        "-nc",
        "-nrd",
        "-nnr",
        "-b",
        "",
        "--dateFormat",
        "%Y-%m-%d",
        "--timeFormat",
        "%H:%M",
        "-po",
        "title,calendarName,allDayEvent,datetime,location,notes",
        "-ps",
        "|@|",
        f"eventsFrom:{start_day.isoformat()}",
        f"to:{end_day.isoformat()}",
    ]
    log(f"[cmd] {' '.join(cmd)}")
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.stderr.strip():
        log(f"[stderr] {proc.stderr.strip()}")
    if proc.returncode != 0:
        log(f"[warn] icalBuddy returncode={proc.returncode}")
    lines = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
    log(f"[stdout lines] {len(lines)}")
    return lines


def clean_line(line: str) -> str:
    return line.replace("\u0001f9e8", "").strip()


def parse_lines(lines: List[str], sample_day: date | None) -> List[Dict[str, Any]]:
    tz = datetime.now().astimezone().tzinfo or timezone.utc
    today = date.today()
    yesterday = today - timedelta(days=1)

    events: List[Dict[str, Any]] = []
    for raw in lines:
        line = clean_line(raw)
        if not line:
            continue
        if "|@|" not in line:
            # fallback: try inline "@YYYY-MM-DD at HH:MM - HH:MM"
            m = re.search(r"@(?P<date>\d{4}-\d{2}-\d{2})\s+at\s+(?P<t1>\d{1,2}:\d{2})\s*-\s*(?P<t2>\d{1,2}:\d{2})", line)
            if not m:
                log(f"[skip] no_attr_sep: {raw}")
                continue
            d = m.group("date")
            t1 = m.group("t1")
            t2 = m.group("t2")
            title_part = line.split("@", 1)[0].strip()
            tail_parts = line.split("@", 2)
            location = tail_parts[2] if len(tail_parts) > 2 else ""
            start_dt = datetime.fromisoformat(f"{d} {t1}:00").replace(tzinfo=tz)
            end_dt = datetime.fromisoformat(f"{d} {t2}:00").replace(tzinfo=tz)
            if sample_day and start_dt.date() != sample_day:
                continue
            events.append(
                {
                    "title": title_part,
                    "calendar": "",
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "allday": False,
                    "location": location,
                    "notes": "",
                }
            )
            continue
        parts = line.split("|@|")
        if len(parts) < 6:
            log(f"[skip] {raw}")
            continue
        title, cal_name, allday_txt, dt_field, location, notes = parts[:6]
        # datetime field from icalBuddy attributes can be single date or date+time span
        # format example: "2025-12-07 00:01 - 00:23" or "2025-12-07"
        allday_flag = str(allday_txt).lower() in ["yes", "true"]

        if " - " in dt_field:
            day_part, times = dt_field.split(" ", 1)
            t1, t2 = times.split(" - ")
            start_dt = datetime.fromisoformat(f"{day_part} {t1}:00").replace(tzinfo=tz)
            end_dt = datetime.fromisoformat(f"{day_part} {t2}:00").replace(tzinfo=tz)
        else:
            start_dt = datetime.fromisoformat(f"{dt_field} 00:00:00").replace(tzinfo=tz)
            end_dt = datetime.fromisoformat(f"{dt_field} 23:59:59").replace(tzinfo=tz)
            allday_flag = True

        if sample_day and start_dt.date() != sample_day:
            continue

        events.append(
            {
                "title": title,
                "calendar": cal_name,
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "allday": allday_flag,
                "location": location,
                "notes": notes,
            }
        )

    log(f"[parsed events] {len(events)}")
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description="抓取一周内的日历事件并写入 data/calendar/")
    parser.add_argument("--start", help="周起始日期 YYYY-MM-DD（默认本周周一）")
    parser.add_argument("--cals", help="限定日历名称（逗号分隔，可含 emoji）")
    parser.add_argument("--debug", action="store_true", help="打印调试信息")
    parser.add_argument("--sample-day", help="仅解析指定日期 YYYY-MM-DD，便于小范围验证")
    args = parser.parse_args()

    # 重置日志
    LOG_FILE.write_text("", encoding="utf-8")

    today = date.today()
    start_day = date.fromisoformat(args.start) if args.start else (today - timedelta(days=today.weekday()))
    end_day = start_day + timedelta(days=7)
    allow_cals = [c.strip() for c in args.cals.split(",")] if args.cals else None
    sample_day = date.fromisoformat(args.sample_day) if args.sample_day else None

    lines = run_icalbuddy(start_day, end_day)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"week-{iso_week_str(start_day)}.txt"
    if raw_path.exists():
        raw_path.unlink()
    raw_path.write_text("\n".join(lines), encoding="utf-8")
    log(f"[raw saved] {raw_path}")

    events = parse_lines(lines, sample_day)

    if allow_cals:
        filtered = [e for e in events if any(cal in e["calendar"] for cal in allow_cals)]
        if filtered:
            events = filtered
        else:
            log(f"[warn] 过滤后无事件，保留全部，filters={allow_cals}, total={len(events)}")

    payload = {
        "week": iso_week_str(start_day),
        "start": datetime.combine(start_day, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
        "end": datetime.combine(end_day, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
        "events": events,
        "count": len(events),
        "source": "icalbuddy",
        "calendars": allow_cals or "all",
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"week-{iso_week_str(start_day)}.json"
    if out_path.exists():
        out_path.unlink()
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写入完成：{out_path}（{len(events)} 条事件）")
    log(f"[done] {out_path} ({len(events)} events)")
    if args.debug:
        print(f"[debug] 事件数：{len(events)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
