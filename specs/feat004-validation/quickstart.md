# 校验与提示快速开始
- 标准化周数据用于校验：`python3 scripts/read_calendar_week.py --week <YYYY-Www> [--input data/calendar/week-<week>.json]`，输出 `data/calendar/normalized-week-<week>.json`，`meta.event_count` 记录事件数。
- 快速比对事件量：`jq '.week|length, .meta.event_count' data/calendar/normalized-week-<week>.json`，长度不一致时回溯源 JSON 或 `fetch_calendar.log`。
- 缺文件/路径错误会直接报错（FileNotFoundError），按提示补齐输入后重跑以避免静默失败。
