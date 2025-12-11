# 计划（FEAT-006-Bear 导出与增量策略）

## 范围与策略
- 数据源：Bear SQLite + 附件；输出到 `data/notes_export/`（gitignore），含正文/附件/manifest。
- 模式：P0 全量导出；P1 标签/时间范围/最近 N 天增量；P2 自然语言指令（“导出上周/标签X”）。
- 去重：note_id + 更新时间（或内容哈希）判定，已存在且未变化则跳过；变更则覆盖。
- 日志：调试阶段将命令/返回码/解析失败写入 `data/notes_export/export_notes.log`，符合宪章14条。

## 里程碑
- M0：落地目录、gitignore 规则、manifest 结构（note_id、updated_at、hash、path）。
- M1：全量导出脚本，可过滤标签/时间范围；支持 dry-run 预览。
- M2：增量导出（依据 manifest 检测变更/新增），自然语言参数解析（标签/日期区间/最近N天）。
- M3：验证与文档：quickstart + 常见问题（权限、路径、无数据占位）。

## 交付物
- `scripts/export_notes.py`（或同名）及复用函数，产出 Markdown/附件、manifest、日志。
- 文档：`docs/bear-integration.md` 补充使用示例；`specs/feat006-bear-export/quickstart.md`（可复用）。
- 示例命令：全量、按标签、按日期、增量模式。

## 风险与对策
- 权限/路径差异：在日志中明确提示缺少 DB/附件路径；允许通过参数覆盖默认路径。
- 重复/漏导：manifest 作为单一真相；落盘前先备份旧文件或使用原子写入。
