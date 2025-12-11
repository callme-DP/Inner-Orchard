#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚合全年日历周文件，生成全年扁平事件列表（支持按体积分片）：
- 输入：data/calendar/week-*.json（默认）或指定目录
- 输出：artifacts/calendar/all-<year>.json 或分片 all-<year>-<idx>.json（事件扁平数组）
- 去重：按 title+start+end，发现重复会记录到 dedup-review.md 供人工确认
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Tuple, Any

BASE = Path(__file__).resolve().parent.parent
DEFAULT_WEEKS_DIR = BASE / "data" / "calendar"
DEFAULT_OUT_DIR = BASE / "artifacts" / "calendar"
DEFAULT_MAX_MB = 5.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="聚合全年日历周文件为按月分组的总表")
    parser.add_argument("--year", type=int, help="目标年份，默认取当前年", default=datetime.now().year)
    parser.add_argument("--weeks-dir", type=Path, default=DEFAULT_WEEKS_DIR, help="周文件目录，默认 data/calendar")
    parser.add_argument("--output", type=Path, help="输出文件路径，默认 artifacts/calendar/all-<year>.json")
    parser.add_argument("--dedup-report", type=Path, help="重复事件报告，默认 artifacts/calendar/dedup-review.md")
    parser.add_argument("--max-mb", type=float, default=DEFAULT_MAX_MB, help="单文件最大体积（MB），超过后按 1-9 分片，默认 5MB")
    parser.add_argument(
        "--exclude-calendars",
        help="排除日历名称（逗号分隔，子串匹配），常见如：中国大陆节假日,生日,Siri建议",
    )
    return parser.parse_args()


def load_week(path: Path) -> Tuple[str, List[Dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    week_label = str(data.get("week") or path.stem)
    events = data.get("events") or []
    return week_label, events


def parse_start(event: Dict[str, Any]) -> datetime | None:
    start_raw = event.get("start")
    if not start_raw:
        return None
    try:
        return datetime.fromisoformat(str(start_raw))
    except Exception:
        return None


def parse_end(event: Dict[str, Any]) -> datetime | None:
    end_raw = event.get("end")
    if not end_raw:
        return None
    try:
        return datetime.fromisoformat(str(end_raw))
    except Exception:
        return None


def dedup_key(event: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    去重键包含标题+开始/结束完整时间（含时区），避免只按日期聚合导致误判。
    """
    start_dt = parse_start(event)
    end_dt = parse_end(event)
    return (
        str(event.get("title") or ""),
        start_dt.isoformat() if start_dt else str(event.get("start") or ""),
        end_dt.isoformat() if end_dt else str(event.get("end") or ""),
    )


def should_exclude(evt: Dict[str, Any], exclude_cals: list[str]) -> bool:
    cal = str(evt.get("calendar") or "")
    return any(token and token in cal for token in exclude_cals)


def parse_week_label(label: str) -> tuple[int, int] | None:
    txt = label or ""
    if txt.startswith("week-"):
        txt = txt[len("week-") :]
    m = re.match(r"(\d{4})-W(\d{2})", txt)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def weeks_are_adjacent(w1: str, w2: str) -> bool:
    a = parse_week_label(w1)
    b = parse_week_label(w2)
    if not a or not b:
        return False
    y1, wk1 = a
    y2, wk2 = b
    if y1 == y2:
        return abs(wk1 - wk2) == 1
    if y1 + 1 == y2 and wk1 in {52, 53} and wk2 == 1:
        return True
    if y2 + 1 == y1 and wk2 in {52, 53} and wk1 == 1:
        return True
    return False


def build_archive(year: int, weeks_dir: Path, exclude_cals: list[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    events: List[Dict[str, Any]] = []
    seen: Dict[Tuple[str, str, str], Tuple[str, str, date]] = {}
    duplicates: List[Dict[str, Any]] = []

    week_files = sorted(weeks_dir.glob("week-*.json"))
    week_pattern = re.compile(r"week-(\d{4})-W\d{2}\.json")

    for wf in week_files:
        match = week_pattern.match(wf.name)
        if not match:
            continue
        week_year = int(match.group(1))
        if week_year not in {year, year - 1, year + 1}:
            # 允许跨年周，后续按事件日期筛选
            pass

        week_label, week_events = load_week(wf)
        for evt in week_events:
            start_dt = parse_start(evt)
            if not start_dt or start_dt.year != year:
                continue
            if exclude_cals and should_exclude(evt, exclude_cals):
                continue
            key = dedup_key(evt)
            if key in seen:
                first_file, first_week, first_date = seen[key]
                same_day = first_date == start_dt.date()
                if same_day and weeks_are_adjacent(first_week, week_label):
                    # 周界重叠导致的重复，不记录在报告中
                    continue
                duplicates.append(
                    {
                        "title": evt.get("title"),
                        "start": evt.get("start"),
                        "end": evt.get("end"),
                        "current_file": str(wf),
                        "first_seen_file": first_file,
                    }
                )
                continue

            seen[key] = (str(wf), week_label, start_dt.date())
            record = dict(evt)
            record["source_week"] = week_label
            record["source_file"] = str(wf)
            events.append(record)

    # 按开始时间排序，便于切片和查询
    events.sort(key=lambda e: e.get("start") or "")
    return events, duplicates


def split_events(events: List[Dict[str, Any]], max_mb: float) -> List[List[Dict[str, Any]]]:
    """按文件体积粗略分片，最多 9 片。"""
    if not events:
        return [events]
    chunks: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    for evt in events:
        current.append(evt)
        size_mb = len(json.dumps(current, ensure_ascii=False)) / (1024 * 1024)
        if size_mb >= max_mb and len(chunks) < 8:
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks


def write_outputs(year: int, events: List[Dict[str, Any]], duplicates: List[Dict[str, Any]], output: Path, dedup_report: Path, max_mb: float, exclude_cals: list[str]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    chunks = split_events(events, max_mb)
    if len(chunks) == 1:
        output.write_text(json.dumps(chunks[0], ensure_ascii=False, indent=2), encoding="utf-8")
        out_paths = [output]
    else:
        out_paths = []
        for idx, chunk in enumerate(chunks, start=1):
            out_path = output.with_name(f"{output.stem}-{idx}{output.suffix}")
            out_path.write_text(json.dumps(chunk, ensure_ascii=False, indent=2), encoding="utf-8")
            out_paths.append(out_path)

    dedup_report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Calendar Dedup Review",
        f"- year: {year}",
        f"- generated: {datetime.now().isoformat(timespec='seconds')}",
        f"- outputs: {', '.join(str(p) for p in out_paths)}",
        f"- exclude_calendars: {', '.join(exclude_cals) if exclude_cals else 'none'}",
        "",
    ]
    if duplicates:
        lines.append("## Duplicates detected (title+start+end)")
        for dup in duplicates:
            lines.append(
                f"- {dup.get('title')} | {dup.get('start')} → {dup.get('end')} | first: {dup.get('first_seen_file')} | dup: {dup.get('current_file')}"
            )
        lines.append("")
        lines.append("请人工确认是否为同一事件，必要时调整源周文件或保留重复。")
    else:
        lines.append("## No duplicates detected (key: title+start+end)")
        lines.append("无需人工处理。")
    dedup_report.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output = args.output or DEFAULT_OUT_DIR / f"all-{args.year}.json"
    dedup_report = args.dedup_report or DEFAULT_OUT_DIR / "dedup-review.md"
    exclude_cals = [c.strip() for c in (args.exclude_calendars or "").split(",") if c.strip()]
    events, duplicates = build_archive(args.year, args.weeks_dir, exclude_cals)
    write_outputs(args.year, events, duplicates, output, dedup_report, args.max_mb, exclude_cals)
    print(f"写入完成：{output}（事件数：{len(events)}，分片：{1 if output.exists() else '多文件'})")
    print(f"重复事件记录：{dedup_report}（{'有' if duplicates else '无'}重复）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
