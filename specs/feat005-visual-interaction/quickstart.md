# 视觉与交互快速开始
- 生成可交互周报：`python3 scripts/build_weekly.py [--calendar data/calendar/week-<ISO周>.json]`，输出 `html/output/weekly.html`（无日历时用 mock）。
- 走查交互：在浏览器打开 `html/output/weekly.html`，依次测试粒度切换（周/月/年）、精力维度切换、周对比显示与缺数据占位。
- 校验类别映射：确认左侧类别卡的时长与日历事件汇总一致，若不符返回日历源检查类别字段。
