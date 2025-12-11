# 日历解析修复快速开始
- 生成本周原始+解析输出：`python3 scripts/fetch_calendar.py --start <周一> [--cals 🍁 个人日常,...]`，产出 `data/calendar/raw/week-<ISO周>.txt` 与 `data/calendar/week-<ISO周>.json`，日志在 `data/calendar/fetch_calendar.log`。
- 小范围验证正则：`python3 scripts/fetch_calendar.py --start <周一> --sample-day YYYY-MM-DD --debug` 仅解析指定日期，查看 `[parsed events]` 与 `[skip]` 统计。
- 查看/排查跳过原因：`tail -n 40 data/calendar/fetch_calendar.log`，根据 `attr_dt_parse_fail` / `fallback_dt_parse_fail` / `no_attr_sep` 记录调整解析规则后重跑。
