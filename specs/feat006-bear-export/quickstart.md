# Bear 导出快速开始
- 全量/标签导出：`python3 scripts/export_bear_notes.py --tag <标签> --output-dir data/notes_export/<tag>`，从本地 Bear SQLite 导出 Markdown、前置元数据与附件链接。
- 增量导出：`python3 scripts/export_bear_notes.py --since-days 1 --output-dir data/notes_export/latest`，仅导出最近 N 天更新的笔记。
- 精确筛选：`python3 scripts/export_bear_notes.py --ids id1,id2 --output-dir data/notes_export/by-id`，按 note identifier 导出；默认 DB/附件路径为 Bear 安装目录，可用 `--db-path`/`--attachments-dir` 覆盖。
