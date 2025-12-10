# FEAT-003-数据管道（接入真实数据源）

## 目标
- 用真实数据替换 mock：日历（本地 JSON/icalBuddy）、ActivityWatch（API）、Mood（本地记录或导出），保持现有接口。

## 范围
- 输入：`data/calendar/week-*.json`、ActivityWatch 聚合、Mood/精力记录。
- 输出：`html/output/weekly.html` 及对应的 JSON/中间文件。
- 接口兼容：沿用现有字段结构，后续渲染无需改动。

## 验收
- 提供一键生成脚本，读取真实数据生成 weekly HTML。
- 缺数据/缺权限时有明确提示并回退 mock/占位。
- 日历类别正确映射到左侧类别卡，时长合计一致。
