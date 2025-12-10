# 时间与精力可视化任务列表（Feat-001）

- T1 数据结构固化：定义日历/ActivityWatch/Mood/突发任务的 JSON schema，并在 mock 数据中保持一致接口。
- T2 生成脚本：`build_weekly.py`/`render_weekly.py` 读取本地数据生成 `html/output/weekly.html`，支持日/周/月/年粒度。
- T3 模板联动：完善粒度切换逻辑，确保柱状、折线、表格同步更新；精力“全部”仅本周四条，单维含上周对比。
- T4 校验提示：生成前检查缺数据/缺权限，渲染后提示耗时对齐或差值。
- T5 真实数据接入：替换 Mock，调用日历/ActivityWatch/Mood（或 MoodExample 导出）填充数据。
- T6 突发任务来源：从日历“突发任务”类别计数，生成本周/上周折线。
- T7 任务生成规则：按 `tasks-guidelines.md` 执行/维护；测试要求若免测需在任务中显式标注【免测】。
