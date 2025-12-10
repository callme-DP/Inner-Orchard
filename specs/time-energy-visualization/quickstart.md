# 时间与精力可视化快速上手（MVP）

## 前置
- 安装并启动 ActivityWatch（含 aw-watcher-web）。
- MoodExample：用于记录每日情绪/精力（或直接用本项目的 `scripts/log_mood.py`）。
- 本项目的 `data/` 目录已在 `.gitignore` 中，确保隐私不入库。

## 步骤
1) 准备日历数据（可先用 Mock）  
   - 创建 `data/calendar/2024-12-09.json`，示例：
   ```json
   [
     {"title":"项目规划","start":"2024-12-09T09:30:00+08:00","end":"2024-12-09T12:00:00+08:00","calendar":"工作","category":"工作","notes":"需求评审"},
     {"title":"深度工作","start":"2024-12-09T13:30:00+08:00","end":"2024-12-09T15:30:00+08:00","calendar":"工作","category":"工作","notes":""},
     {"title":"邮件/IM 处理","start":"2024-12-09T15:30:00+08:00","end":"2024-12-09T16:12:00+08:00","calendar":"沟通/会议","category":"沟通/会议","notes":""}
   ]
   ```

2) 拉取 ActivityWatch 数据  
   ```bash
   python scripts/fetch_aw.py --date 2024-12-09
   ```
   - 输出：`data/activitywatch/2024-12-09.json`（包含事件与聚合）。

3) 记录精力/Mood  
   - 方式A：使用 MoodExample 导出到 `data/mood/`。  
   - 方式B：直接追加记录：
   ```bash
   python scripts/log_mood.py --day 2024-12-09 --slot morning --score 7 --tags "focus,calm" --notes "晨跑后专注"
   python scripts/log_mood.py --day 2024-12-09 --slot noon --score 6
   python scripts/log_mood.py --day 2024-12-09 --slot evening --score 5 --tags "疲劳"
   ```
   - 输出：`data/mood/log.jsonl`

4) 汇总与渲染（占位说明）  
   - 后续将提供 `build_weekly.py`/`render_weekly.py`：读取上述文件，生成周级 JSON -> `html/output/weekly.html`，并支持日/周/月/年切换。  
   - 目前可使用 Mock 数据先行设计与验证模板。

## 设计提示
- 布局参考：左（应用类别耗时：按日历类别聚合，随日/周/月/年切换，右侧环比百分比），中（精力趋势折线：本周/上周切换，“全部”=本周四条，单维=本周+上周对比），右（突发任务折线：默认周，本周 vs 上周），下方（日历事件表格：随粒度联动）。
- 对比维度：周视图支持本周 vs 上周；“全部”精力维度仅显示本周四条折线，单维显示本周 + 上周对比；突发任务默认周对比。
- 校验：渲染前检查数据存在性；渲染后显示总耗时与差值。
