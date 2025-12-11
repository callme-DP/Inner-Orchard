# 数据管道快速开始
- 准备日历数据：先用 FEAT-002 生成 `data/calendar/week-<ISO周>.json`（缺失时脚本会 fallback mock）。
- 生成周报 HTML：`python3 scripts/build_weekly.py [--calendar data/calendar/week-<ISO周>.json]`，输出 `html/output/weekly.html`，meta 会标注日历来源。
- 预览结果：用浏览器打开 `html/output/weekly.html`，确认左侧类别时长、情绪/事件分布等是否加载正常（无日历时自动使用 mock）。
