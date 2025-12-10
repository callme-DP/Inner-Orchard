# 任务（FEAT-006-笔记导出与增量策略）

- T1 目录与忽略：创建 `data/notes_export/`（含附件子目录、manifest、日志），确认 `.gitignore` 已覆盖。
- T2 manifest 设计：定义字段（note_id、title、tags、updated_at、hash、path、attachments[]），实现读写工具。
- T3 全量导出：实现脚本读取 Bear DB，导出全部 Markdown/附件，落盘 manifest，日志记录命令/返回码。
- T4 过滤导出：支持标签/日期范围/最近 N 天参数，dry-run 列表预览将被导出的笔记。
- T5 增量导出：对比 manifest 检测新增/变更/删除，变更覆盖写入，跳过未变。
- T6 自然语言入口：接受“导出上周笔记/导出标签X/导出最近3天”式参数，转换为过滤条件。
- T7 文档与示例：编写 quickstart（命令示例、路径、权限提示、常见错误），在 `docs/bear-integration.md` 引用。
