# 任务生成规则（占位，待对齐宪章 4.4 测试策略）

> 用于生成/审查本 Future 的任务，后续如有新的测试需求，请告知，我会同步维护本规则并回填宪章相关段落。

## 输入
- 设计来源：`/specs/time-energy-visualization/` 下的 `spec.md`、`plan.md`、`tasks.md`、`research.md` 等。

## 前置材料
- 必读：`spec.md`、`plan.md`、`tasks.md`、`research.md`。
- 数据/接口：`mock-data/*.json`、`html/v1/weekly_mock.html`、`scripts/`。
- 宪章参考：`.specify/memory/constitution.md`（测试策略将落在 4.4 段落，当前为占位）。

## 测试要求（占位）
- 默认为“需测试”状态，请根据具体任务确认：
  - 需要测试：数据管道/聚合校验、渲染逻辑、校验提示。
  - 不需要测试：纯文档、样式微调（无逻辑影响）。
- 如用户明确“无需测试”，在任务描述中注明【免测】。

## 组织方式
- 任务按故事/模块分组，避免跨组依赖。
- 可并行项标注 `[P]`，无依赖可并行执行。

## 格式
- `ID [P?] [Story] 描述`
  - `ID`：任务编号（如 T1、T2）。
  - `[P]`：可并行时标注。
  - `[Story]`：所属故事/模块（如 日历管道、AW聚合、渲染联动）。
  - 描述中写明确切文件路径。

## 路径约定
- 数据：`data/`（输出），`specs/time-energy-visualization/mock-data/`（示例）。
- 模板：`html/v1/weekly_mock.html`；输出：`html/output/weekly.html`。
- 脚本：`scripts/`（如 `build_weekly_mock.py`、`fetch_calendar.py`）。

## 待办
- 将测试策略细则与 `.specify/memory/constitution.md` 的 4.4 段落对齐，并根据实际测试需求更新此处“测试要求”。
