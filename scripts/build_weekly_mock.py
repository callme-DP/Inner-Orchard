#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 mock 数据组合并注入到 HTML 模板，生成周视图占位页面。
输入：specs/time-energy-visualization/mock-data 下的 JSON
输出：html/output/weekly.html
"""

from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MOCK_DIR = BASE / "specs" / "time-energy-visualization" / "mock-data"
TEMPLATE = BASE / "html" / "v1" / "weekly_mock.html"
OUT_DIR = BASE / "html" / "output"
OUT_FILE = OUT_DIR / "weekly.html"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def merge_data() -> dict:
    aw = load_json(MOCK_DIR / "activitywatch.aggregate.json")
    calendar = load_json(MOCK_DIR / "calendar.mock.json")
    mood = load_json(MOCK_DIR / "mood.week.json")
    incidents = load_json(MOCK_DIR / "incidents.week.json")
    return {
        "periods": ["day", "week", "month", "year"],
        "activitywatch": aw,
        "calendar": calendar,
        "mood": mood,
        "incidents": incidents,
    }


def build():
    data = merge_data()
    raw_html = TEMPLATE.read_text(encoding="utf-8")
    html = raw_html.replace("__MOCK_DATA__", json.dumps(data, ensure_ascii=False, indent=2))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(html, encoding="utf-8")
    print(f"生成完成：{OUT_FILE}")


if __name__ == "__main__":
    build()
