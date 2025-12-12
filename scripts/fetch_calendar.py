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
from datetime import date, datetime, timedelta, timezone, time
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


def run_icalbuddy(start_day: date, end_day: date, include_cals: List[str] | None, exclude_cals: List[str] | None) -> List[str]:
    # 使用带属性输出的单行模式，便于解析
    cmd = [
        "icalBuddy",
        "-npn",
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
    if include_cals:
        cmd[1:1] = ["-ic", ",".join(include_cals)]
    if exclude_cals:
        cmd[1:1] = ["-ec", ",".join(exclude_cals)]
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


def resolve_date(token: str, today: date, yesterday: date) -> date | None:
    txt = token.strip().lower()
    if txt == "today":
        return today
    if txt == "yesterday":
        return yesterday
    try:
        return date.fromisoformat(token.strip())
    except ValueError:
        return None


def parse_time_part(txt: str) -> time | None:
    try:
        return datetime.strptime(txt.strip(), "%H:%M").time()
    except ValueError:
        return None


def parse_datetime_span(dt_field: str, tz: timezone, today: date, yesterday: date) -> tuple[datetime, datetime, bool] | None:
    """Parse datetime span supporting absolute dates and relative today/yesterday."""
    field = dt_field.strip()
    # full span with optional second date, with/without "at"
    span_patterns = [
        r"(?P<d1>[\w-]+)\s+(?:at\s+)?(?P<t1>\d{1,2}:\d{2})\s*-\s*(?:(?P<d2>[\w-]+)\s+at\s+)?(?P<t2>\d{1,2}:\d{2})",
        r"(?P<d1>[\w-]+)\s+(?P<t1>\d{1,2}:\d{2})\s*-\s*(?:(?P<d2>[\w-]+)\s+)?(?P<t2>\d{1,2}:\d{2})",
    ]
    for pat in span_patterns:
        m = re.match(pat, field, flags=re.IGNORECASE)
        if not m:
            continue
        d1 = resolve_date(m.group("d1"), today, yesterday)
        d2 = resolve_date(m.group("d2") or m.group("d1"), today, yesterday)
        t1 = parse_time_part(m.group("t1"))
        t2 = parse_time_part(m.group("t2"))
        if not (d1 and d2 and t1 and t2):
            return None
        start_dt = datetime.combine(d1, t1, tzinfo=tz)
        end_dt = datetime.combine(d2, t2, tzinfo=tz)
        return start_dt, end_dt, False

    # date only or date with single time -> treat as all-day if no time
    parts = field.split()
    if not parts:
        return None
    d = resolve_date(parts[0], today, yesterday)
    if not d:
        return None
    if len(parts) > 1:
        t1 = parse_time_part(parts[1]) or time(0, 0)
        start_dt = datetime.combine(d, t1, tzinfo=tz)
        end_dt = datetime.combine(d, t1, tzinfo=tz)
        return start_dt, end_dt, False
    start_dt = datetime.combine(d, time(0, 0), tzinfo=tz)
    end_dt = datetime.combine(d, time(23, 59, 59), tzinfo=tz)
    return start_dt, end_dt, True


def clean_value(txt: str) -> str:
    return re.sub(r"^(?:notes?|url):\s*", "", (txt or "").strip(), flags=re.IGNORECASE)


def split_title_and_calendar(raw_title: str) -> tuple[str, str]:
    """
    将形如 "title | 26分钟 (CalendarName)" 拆为标题与日历名。
    - 去掉右侧的持续时间片段（" | xxx"）
    - 提取末尾括号内的日历名
    """
    txt = raw_title.strip()
    cal_name = ""
    # 提取末尾括号内的日历名
    m = re.search(r"\(([^)]+)\)\s*$", txt)
    if m:
        cal_name = m.group(1).strip()
        txt = txt[: m.start()].strip()
    # 去掉持续时间片段（一般在括号前面）
    if "|" in txt:
        txt = txt.split("|", 1)[0].strip()
    return txt, cal_name


def split_location_notes(tail_parts: List[str]) -> tuple[str, str]:
    if not tail_parts:
        return "", ""
    cleaned_parts = []
    for part in tail_parts:
        val = clean_value(part)
        if val:
            cleaned_parts.append(val)
    if not cleaned_parts:
        return "", ""
    location = cleaned_parts[0]
    notes = "@".join(p for p in cleaned_parts[1:] if p)
    return location, notes


def parse_lines(lines: List[str], sample_day: date | None) -> List[Dict[str, Any]]:
    tz = datetime.now().astimezone().tzinfo or timezone.utc
    today = date.today()
    yesterday = today - timedelta(days=1)

    events: List[Dict[str, Any]] = []
    total_lines = len(lines)
    skip_count = 0
    for raw in lines:
        line = clean_line(raw)
        if not line:
            continue
        parsed = None
        if "|@|" in line:
            parts = line.split("|@|")
            while len(parts) < 6:
                parts.append("")
            title, cal_name, allday_txt, dt_field, location, notes = parts[:6]
            dt_span = parse_datetime_span(dt_field, tz, today, yesterday)
            if not dt_span:
                log(f"[skip] attr_dt_parse_fail: {raw}")
            else:
                start_dt, end_dt, allday_flag = dt_span
                allday_flag = allday_flag or str(allday_txt).lower() in ["yes", "true"]
                parsed = {
                    "title": title,
                    "calendar": cal_name,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "allday": allday_flag,
                    "location": clean_value(location),
                    "notes": clean_value(notes),
                }
        else:
            title_part, sep, rest = line.partition("@")
            if not sep:
                log(f"[skip] no_attr_sep: {raw}")
            else:
                segments = rest.split("@")
                dt_field = segments[0]
                tail_parts = segments[1:]
                dt_span = parse_datetime_span(dt_field, tz, today, yesterday)
                if not dt_span:
                    log(f"[skip] fallback_dt_parse_fail: {raw}")
                else:
                    start_dt, end_dt, allday_flag = dt_span
                    location, notes = split_location_notes(tail_parts)
                    title_clean, cal_name = split_title_and_calendar(title_part)
                    parsed = {
                        "title": title_clean,
                        "calendar": cal_name,
                        "start": start_dt.isoformat(),
                        "end": end_dt.isoformat(),
                        "allday": allday_flag,
                        "location": location,
                        "notes": notes,
                    }

        if not parsed:
            skip_count += 1
            continue

        if sample_day and datetime.fromisoformat(parsed["start"]).date() != sample_day:
            continue

        events.append(parsed)

    log(f"[parsed events] {len(events)} / {total_lines} (skipped {skip_count})")
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description="抓取一周内的日历事件并写入 data/calendar/")
    parser.add_argument("--start", help="周起始日期 YYYY-MM-DD（默认本周周一）")
    parser.add_argument("--end", help="结束日期 YYYY-MM-DD（默认 start+7 天）")
    parser.add_argument("--cals", help="限定日历名称（逗号分隔，可含 emoji）")
    parser.add_argument("--exclude-cals", help="排除日历名称（逗号分隔，可含 emoji）")
    parser.add_argument("--year", type=int, help="抓取整个年份，按周输出 week-*.json")
    parser.add_argument("--debug", action="store_true", help="打印调试信息")
    parser.add_argument("--sample-day", help="仅解析指定日期 YYYY-MM-DD，便于小范围验证")
    args = parser.parse_args()

    today = date.today()
    start_day_default = today - timedelta(days=today.weekday())
    start_day = date.fromisoformat(args.start) if args.start else start_day_default
    end_day = date.fromisoformat(args.end) if args.end else (start_day + timedelta(days=7))
    allow_cals = [c.strip() for c in args.cals.split(",")] if args.cals else None
    exclude_cals = [c.strip() for c in args.exclude_cals.split(",")] if args.exclude_cals else None
    sample_day = date.fromisoformat(args.sample_day) if args.sample_day else None

    # 重置日志
    LOG_FILE.write_text("", encoding="utf-8")

    def run_one_week(week_start: date) -> int:
        week_end = week_start + timedelta(days=7)
        lines = run_icalbuddy(week_start, week_end, allow_cals, exclude_cals)
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        raw_path = RAW_DIR / f"week-{iso_week_str(week_start)}.txt"
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
            "week": iso_week_str(week_start),
            "start": datetime.combine(week_start, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
            "end": datetime.combine(week_end, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
            "events": events,
            "count": len(events),
            "source": "icalbuddy",
            "calendars": allow_cals or "all",
            "excluded_calendars": exclude_cals or [],
        }

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUT_DIR / f"week-{iso_week_str(week_start)}.json"
        if out_path.exists():
            out_path.unlink()
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"写入完成：{out_path}（{len(events)} 条事件）")
        log(f"[done] {out_path} ({len(events)} events)")
        if args.debug:
            print(f"[debug] 事件数：{len(events)}")
        return len(events)

    if args.year:
        year = args.year
        first_day = date(year, 1, 1)
        week_start = first_day - timedelta(days=first_day.weekday())
        total_events = 0
        while week_start.year <= year or (week_start + timedelta(days=7)).year == year:
            total_events += run_one_week(week_start)
            week_start += timedelta(days=7)
        print(f"全年抓取完成：{year}，累计事件 {total_events}")
    else:
        run_one_week(start_day)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
