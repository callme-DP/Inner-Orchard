# System Governance Spec

目的：让 AI 明确各类系统文档的角色、权限与升级路径，避免误改不可变约束，并知道何时提议/求证。

## 文档角色与权限
- `constitution.md`（只读）：系统级不可变约束，任何改动必须人工主导，AI 不得修改。
- `AGENTS.md`（建议/提议）：执行规范和合作约定，可提议修改或补充，但需提示人类确认。
- 根级 `specs/spec.md`（系统级 spec）：跨 storage/跨 feature 的共识性约定；AI 可提出草案变更，需经人类确认后再改。
- 各 `specs/<feature>/spec.md`（功能级 spec）：仅对对应 feature 生效；如内容上升为跨 storage/跨 feature，需提议提升到根级 spec。
- `docs/system-map.md`（系统地图）：已确认的稳定能力/结构的共识映射，AI 只能在满足条件时提议更新，不直接修改。

## 什么是“系统级”并应升入根级 spec
- 跨 storage（如 artifacts/、data/ 等目录）或跨多个 feature/模块的约定。
- 影响全局命名/目录/权限/安全策略/交互准则的规则。
- 架构桥/双轨协作等影响多条工作流的流程规范。

## 何时提议更新 system-map.md（仅提议，不直接改）
- 出现新的稳定能力/模块/接口，已落地且不再是实验性质。
- 现有模块的结构或依赖关系发生调整且经人类确认。
- 跨 storage/跨 feature 的路由或数据流有确认的变更。

## AI 对各文档的操作权限
- 只读：`constitution.md`。
- 提议修改：`AGENTS.md`、`docs/system-map.md`（需满足条件）、根级 `specs/spec.md`。
- 可草拟/编辑：各 feature 下的 `spec.md`、`plan.md`、`tasks.md`，以及新增的本文件。
- 升级路径：发现功能级 spec 具备系统级性质时，先在本文件或根级 spec 起草提议，提示人类确认后再升级。

## 必须停下询问人类的情形
- 牵涉系统结构/架构调整（模块拆分/合并、总数据流变更）。
- 跨 storage 的抽象或全局命名/权限策略变更。
- 影响长期约束、不可逆的治理规则调整（如修改 constitution 约束、全局安全/合规要求）。
- 需要将未稳定的能力写入 `docs/system-map.md` 时。

## system-map.md 的定位
- 是“系统能力与结构的当前共识地图”，只收录已确认且稳定的模块/接口/依赖。
- 不是临时想法或实验记录；草案/实验应停留在 feature 级 spec/plan/backlog 中，确认稳定后再提议写入。***
