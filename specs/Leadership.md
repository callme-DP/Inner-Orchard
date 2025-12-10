# Leadership 对齐记录

## 2025-12-10 feat-009 反思目录命名与入库范围
- 问题摘要：日/周反思目录的命名（file-reflect-and-summary）与是否纳入 Git 记录存在反复沟通。
- 之前观点（你）：希望保留日/周反思、模板 mtime 缓存，但不希望产物进入仓库；目录命名需与文档 AI 协作区分。
- 之前处理（我）：曾将反思目录、log 纳入 git 并改名，后被要求撤销；造成多次往返。
- 最新共识：目录改为 `specs/feat-009-file-reflect-and-summary/` 仅本地使用，已在 `.git/info/exclude` 忽略；git 只保留总览条目说明，不追踪 daily/weekly 产物或模板缓存。
- 待办提醒：日模板（ID 146EF927-021D-4BD8-B70B-1377605704D6）尚未导出到 `artifacts/bear-notes/`；如需同步其他机器，请手动添加相同忽略规则。
