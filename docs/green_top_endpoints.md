## Green Top View API

### Sunburst（知识点掌握旭日图）
- **Endpoint**: `GET /api/green/top/sunburst`
- **Query Params**:
  - `class`: 例如 `Class1`
  - `student_ID`: 学生唯一 ID
- **Response**:
```json
{
  "class": "Class1",
  "student": "0088dc183f73c83f763e",
  "sunburst": {
    "name": "知识体系",
    "children": [
      {
        "name": "m3D1v",
        "mastery": 0.82,
        "value": 12,
        "children": [
          {
            "name": "m3D1v_r1d7fr3l",
            "mastery": 0.76,
            "value": 5,
            "children": [
              { "name": "Question_3Mw...", "mastery": 0.9, "value": 1 }
            ]
          }
        ]
      }
    ]
  }
}
```
- **说明**：
  - `mastery` 均为 0~1 浮点数，前端可映射颜色。
  - `value` 可用于扇区面积（为题目数量或子节点数量）。
  - 若某知识点缺少子层数据，会直接挂载题目叶子节点。

### 批量 Sunburst（班级全部学生）
- **Endpoint**: `GET /api/green/top/sunburst/batch`
- **Query Params**:
  - `class`: 班级标识（必填）
- **Response**:
```json
{
  "class": "Class1",
  "students": [
    {
      "student_ID": "8b6d1125760bd3939b6e",
      "sunburst": { ... 与单个接口相同 ... }
    }
  ]
}
```
- **说明**：
  - 后端会遍历该班在 `SubmitRecord-Class*.csv` 中出现的所有 `student_ID`。
  - 如果个别学生没有掌握数据会被自动跳过。
  - 前端可根据需要一次性加载或懒加载各学生的旭日图。

### 数据来源 & 预处理
| 文件 | 作用 |
| --- | --- |
| `mastery/individual_title_mastery.csv` | 题目层掌握度，生成旭日图叶子 |
| `mastery/individual_sub_knowledge_mastery.csv` | 子知识点/知识点掌握度，用于旭日中间层 |
| `Data_TitleInfo.csv` | `title_ID -> (knowledge, sub_knowledge)` 映射 |
| `Data_SubmitRecord/SubmitRecord-Class*.csv` | 获取班级中包含的学生 ID 列表（如需课堂筛选，可在后端扩展） |

### 前端提示
- Sunburst 使用 `series.type = 'sunburst'`，`data` 直接填入 `sunburst` 节点即可。

