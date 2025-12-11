# 计划（FEAT-002-日历解析修复）

## 步骤
1) 保留原始输出：调用 icalBuddy，保存 `data/calendar/raw/week-<ISO周>.txt`。
2) 小范围验证：新增 `--sample-day` 仅解析指定日，快速迭代正则。
3) 宽松解析：截断 `@url/notes:`，支持 yesterday/today/绝对日期时间段；解析失败行写日志。
4) 过滤策略：白名单过滤，若过滤后为空则保留全部并记录。
5) 全量生成：去掉 sample-day，生成 `week-<ISO周>.json`，验证 count 与原始行数匹配度。
6) 年度归档：聚合 `week-*.json` 到 `artifacts/calendar/all-<year>.json`（按月分组，去重并输出人工复核报告）。

## 设计
- 归档调度：日/周复盘触发自动增量（每日 23:59:59 同步当天；周日 23:59:59 补齐当周），与手动指令共存。
- 多源扩展：未来联动 Reminders/任务列表并入归档，保持字段兼容。
- 增量策略：明确“新增 vs 更新”判定（例如按 start+end+title 或 UID），避免重复同时保留变更。
- 存储分片：按年份/月分片滚动归档（如 all-<year>.json 或 all-<year>-<month>.json），控制单文件体积。
- 监控与告警：归档失败或重复事件超阈值时提示人工检查。

## 验证
- 在本机运行 sample-day，检查日志 `[skip]` 占比；解析正常后全量生成。
- 记录解析成功/失败行数到日志，手动 spot check。
