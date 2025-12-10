# 计划（FEAT-002-日历解析修复）

## 步骤
1) 保留原始输出：调用 icalBuddy，保存 `data/calendar/raw/week-<ISO周>.txt`。
2) 小范围验证：新增 `--sample-day` 仅解析指定日，快速迭代正则。
3) 宽松解析：截断 `@url/notes:`，支持 yesterday/today/绝对日期时间段；解析失败行写日志。
4) 过滤策略：白名单过滤，若过滤后为空则保留全部并记录。
5) 全量生成：去掉 sample-day，生成 `week-<ISO周>.json`，验证 count 与原始行数匹配度。

## 验证
- 在本机运行 sample-day，检查日志 `[skip]` 占比；解析正常后全量生成。
- 记录解析成功/失败行数到日志，手动 spot check。
