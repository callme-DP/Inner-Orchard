# SpecKit 总览（Futures 汇总）

## 目标
- 串联 `specs/` 下的各个 Future/Feature，作为总索引与约定。
- 保持 Spec→Clarify→Plan→Tasks→Implement→Test 流程；发现架构/双轨问题时使用“架构桥”约定。

## 当前 Futures
- `feat002-calendar-parsing/`：日历解析修复（属性输出、备注/类别解析等）。
- `feat003-data-pipeline/`：接入真实日历/ActivityWatch/Mood 替换 mock。
- `feat004-validation/`：校验与提示（权限/缺数据/耗时对齐/备注）。
- `feat005-visual-interaction/`：粒度切换、精力维度切换、周对比、缺数据占位；按 phase 拆分 bear/reminder/calendar 可视化（各有 plan/spec/task）。
- `feat006-bear-export/`：Bear 笔记全量/增量导出与 manifest 去重。
- `feat007-cognitive-leap/`（待建）：认知跃迁识别与可视化。
- `feat008-task-management/`（待建）：任务/提醒多维视图。
- `file-reflect-and-summary/`：日/周反思与摘要（文档 AI 协作，不含功能代码，产物不入库）。
- `time-energy-visualization/`：总体可视化规范与快速上手。

## 架构桥 / 双轨协作
- 触发条件：实现过程中发现架构/跨域问题，但不影响当前 deliverable。
- 标准响应（三句话）：
  1) 当前 Sprint 状态：保持不变，继续。
  2) 架构发现：提醒系统需要在下一阶段重构。
  3) 影响范围：不会影响当前 deliverable，但会新增 RFC + Backlog。
- 记录方式：
  - 在本文件“Architecture Notes”追加条目，指向 `specs/rfc-<主题>/` 或相关 feature 下的 `rfc.md`/`backlog.md`。
  - 不修改当前 Feature 范围/承诺；必要的临时绕过需标注。

## 提示词/流程
- Specify/Clarify：`/speckit.specify <一句话目标>` → `/speckit.clarify`
- Plan/Tasks：`/speckit.plan`（输出 plan.md + tasks.md）
- Analyze/Test：`/speckit.analyze` 或手动校验；缺数据/权限需提示
- 架构桥：当发现架构问题时，用上述三句话报告 + 建 RFC/Backlog，并在 Architecture Notes 记录。

## Architecture Notes（占位）
- 待有架构发现时在此追加。
