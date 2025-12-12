# 任务（FEAT-002-日历解析修复）

## Phase 1：解析稳态
- T1 保存原始输出：落盘 `data/calendar/raw/week-<ISO周>.txt`，供溯源。
- T2 原始样本分析：跑一周 TXT + 日志，归纳命名/时间段/尾部噪声规则。
- T3 小范围验证：`--sample-day` 仅解析指定日，迭代正则。
- T4 宽松解析：支持 yesterday/today/跨日时间段，清洗 `@url/notes:`，失败落 `[skip]` 日志。
- T5 过滤策略：白名单过滤，过滤后为空则保留全部并记录 warn。
- T6 首次全量生成：抓取目标年份的全部事件，产出年度归档 `artifacts/calendar/all-<year>.json`（必要时经过周级中间文件），校验条数与原始输出匹配度。

## Phase 2：归档与去重
- T7 年度归档：聚合 `week-*.json` 输出 `artifacts/calendar/all-<year>.json`（扁平数组，支持分片，重跑覆盖）。
- T8 去重报告：按 `title+start+end` 生成 `artifacts/calendar/dedup-review.md`，人工确认并决定是否清洗源数据。

## Phase 3：聚合与渲染
- T9 聚合算法：基于归档数据按日/周/月/年及“上周”范围聚合，计算同比百分比与折线对比。
- T10 渲染调整：前端增加 day 视图（默认今日），类别文案改为“日历类别”，数据源切换为聚合结果，移除 mock 依赖。

## Phase 4：扩展调研
- T11 调研接入 ActivityWatch：形成时间轨迹聚合方案（日/周/月/年）。
- T12 调研接入 Mood 数据：明确情绪数据结构与聚合方式，预留与日历的联动点。
