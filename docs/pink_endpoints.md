## 粉色视图后端接口说明

### 1. 接口概览
| 视图 | 路径 | 方法 | 说明 |
| --- | --- | --- | --- |
| 题目匹配热力图 | `GET /api/pink/heatmap` | GET | 返回热力图所需坐标轴标签与核心数据 |
| 题目综合表现气泡图 | `GET /api/pink/bubbles` | GET | 返回每道题的提交量、分值、平均用时/内存与效率指标 |
| 三维度答题状态折线图 | `GET /api/pink/state-trends` | GET | 返回按时间/知识点/编程语言的状态占比序列 |

所有接口均无需 query 参数，直接访问即可获取 JSON 数据。

---

### 2. 数据结构

#### `/api/pink/heatmap`
```json
{
  "heatedConfig": {
    "xAxisLabels": ["b3C9s", "g7R2j", "..."],
    "yAxisLabels": ["Q_01", "Q_02", "..."]
  },
  "heatmapCoreData": [
    [xIndex, yIndex, "Q_01", "Question_*", "知识点", "子知识点", matchIndex(1-10), correctRate(%), discrimination]
  ]
}
```
* `xAxisLabels` 为主知识点；`yAxisLabels` 为题目别名（`Q_xx`），前端可直接展示。
* `heatmapCoreData` 每行依次提供坐标索引、题目原始 ID、知识点信息以及匹配度、正确率、区分度。

#### `/api/pink/bubbles`
```json
{
  "bubbleData": [
    {
      "title_ID": "Question_*",
      "knowledge": "r8S3g",
      "score": 4,
      "submission_count": 1234,
      "timeconsume": 36.8,
      "memory": 312.5,
      "times_efficiency": 78.3,
      "ram_efficiency": 81.2,
      "comprehensive_efficiency": 79.8
    }
  ],
  "xAxisLabels": ["r8S3g", "t5V9e", "..."]
}
```
* `score` 来自 `Data_TitleInfo.csv`（题目满分），与提交记录中的得分不同。
* `timeconsume`/`memory` 为所有班级合并后的平均值（毫秒 / KB）。
* `times_efficiency`、`ram_efficiency` 为相对效率（该题平均值 ÷ 全部题平均值 × 100）；综合效率为两者平均。

#### `/api/pink/state-trends`
```json
{
  "dimensionData": {
    "time": {
      "xLabels": ["第1周(2023-08-28)", "..."],
      "stateData": [
        { "stateCode": "Absolutely_Correct", "ratios": [25.4, 23.6, ...] },
        ...
      ]
    },
    "knowledge": { "xLabels": ["b3C9s", "g7R2j", "..."], "stateData": [...] },
    "method": { "xLabels": ["Method_5Q4...", "..."], "stateData": [...] }
  }
}
```
* 覆盖 12 种答题状态，`ratios` 为百分数（保留 1 位小数）。
* 时间维度按周聚合，周标签自动基于提交记录的时间戳生成。

---

### 3. 数据来源与预处理
| 文件 | 主要字段 | 用途 |
| --- | --- | --- |
| `data/Data_TitleInfo.csv` | `title_ID`, `score`, `knowledge`, `sub_knowledge` | 题目元数据、热力图/气泡图共享 |
| `data/Data_SubmitRecord/SubmitRecord-Class*.csv` | `title_ID`, `state`, `time`, `method`, `memory`, `timeconsume` 等 | 所有班级提交记录，气泡图与折线图使用 |
| `data/mastery/class_title_mastery.csv` | `score_rate`, `score_rate_norm`, `title_mastery_score` | 热力图维度指标（匹配度/正确率/区分度） |

后端在 `pink_views.py` 中统一做了以下预处理：
1. 所有 CSV 读取时去除 UTF-8 BOM、前后空格，自动匹配大小写差异的列名（`Score`/`score`/`SCORE` 均可）。
2. 提交记录中的 `score` 字段仅用于判分统计，与题目分值区分开。气泡图里使用 `title_score` 保留题目原始分值。
3. `timeconsume`、`memory` 在聚合前会转为数值，无法转换的统一视为缺失并在求平均时跳过。
4. 答题状态仅保留以下 12 种值：`Absolutely_Correct`, `Absolutely_Error`, `Partially_Correct`, `Error1` ~ `Error9`，其它状态会被过滤掉。

---

### 4. 前端对接建议
1. **热力图**：`heatedConfig` 中的坐标直接作为 ECharts `xAxis.data` / `yAxis.data`，`heatmapCoreData` 可转为 `series.data`。
2. **气泡图**：`xAxisLabels` 可作为横轴类别；`bubbleData` 中的 `knowledge` 也可以用于分组或 tooltip 显示。
3. **折线图**：三个维度结构一致，可根据 `dimensionData` 中的键动态渲染多组折线。`stateCode` 需与颜色图例保持一致。
4. 接口均为 GET 请求，无需鉴权；如需缓存可在前端自行 memoize。

如需调整返回结构或追加筛选条件，可与后端约定新增 query 参数（例如按班级过滤），再在 `pink_views.py` 做对应改动。

