# 4.2 个性化学习行为模式 API 接口文档

## 概述

本文档定义了4.2部分（个性化学习行为模式）所需的所有API接口。这些接口用于支持蓝色框的可视化展示，包括学习行为特征提取、学习者画像展示等功能。

---

## 接口列表

### 1. 获取可用月份列表

**接口地址：** `GET /api/learning-profile/available-months`

**请求参数：**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| class_name | string | 否 | 班级名称，用于获取该班级的可用月份 |
| student_id | string | 否 | 学习者ID，用于获取该学习者的可用月份 |

**说明：**
- 如果同时提供 `class_name` 和 `student_id`，优先使用 `student_id`
- 如果都不提供，返回所有可用月份

**响应示例：**
```json
{
  "months": [
    "2024-01",
    "2024-02",
    "2024-03",
    "2024-04"
  ]
}
```

---

### 2. 获取学习行为特征（蓝色框1 - Tab 1: 基础特征）

**接口地址：** `GET /api/learning-profile/behavior-features`

**请求参数：**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| student_id | string | 否 | 学习者ID，不传则返回群体数据 |
| class_name | string | 否 | 班级名称，用于群体分析 |
| month | string | 否 | 月份筛选（格式：YYYY-MM），不传则返回所有月份聚合数据 |

**响应示例：**
```json
{
  "submit_count": 156,
  "active_days": 23,
  "question_count": 45,
  "correct_ratio": 0.85,
  "pattern": "探索尝试型",
  "pattern_ratio": {
    "submit_ratio": 0.92,
    "active_ratio": 0.88,
    "question_ratio": 0.79,
    "correct_ratio": 0.85
  },
  "comparison": {
    "submit_count_avg": 120,
    "active_days_avg": 18,
    "question_count_avg": 35,
    "correct_ratio_avg": 0.78
  }
}
```

**字段说明：**
- `submit_count`: 提交次数
- `active_days`: 活跃天数
- `question_count`: 答题数
- `correct_ratio`: 正确占比
- `pattern`: 学习模式（探索尝试型/广泛多样型/集中针对型）
- `pattern_ratio`: 模式分类的相对比例
- `comparison`: 与平均值的对比数据（用于雷达图）

---

### 3. 获取学习模式分布（蓝色框1 - Tab 2: 学习模式）

**接口地址：** `GET /api/learning-profile/pattern-distribution`

**请求参数：**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| class_name | string | 是 | 班级名称 |
| month | string | 否 | 月份筛选（格式：YYYY-MM） |

**响应示例：**
```json
{
  "patterns": {
    "探索尝试型": 15,
    "广泛多样型": 8,
    "集中针对型": 12
  },
  "total": 35,
  "distribution": [
    {
      "pattern": "探索尝试型",
      "count": 15,
      "percentage": 42.86
    },
    {
      "pattern": "广泛多样型",
      "count": 8,
      "percentage": 22.86
    },
    {
      "pattern": "集中针对型",
      "count": 12,
      "percentage": 34.29
    }
  ]
}
```

---

### 4. 获取编程方法偏好（蓝色框1 - Tab 3: 编程方法）

**接口地址：** `GET /api/learning-profile/method-preference`

**请求参数：**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| student_id | string | 否 | 学习者ID，不传则返回群体数据 |
| class_name | string | 否 | 班级名称，用于群体分析 |
| month | string | 否 | 月份筛选（格式：YYYY-MM） |
| top_n | int | 否 | 返回前N种方法，默认5 |

**响应示例：**
```json
{
  "method_distribution": [
    {
      "method": "Method_Cj9Ya2R7fZd6xs1q5mNQ",
      "method_name": "方法1",
      "count": 45,
      "ratio": 0.35,
      "percentage": 35.0
    },
    {
      "method": "Method_gj1NLb4Jn7URf9K2kQPd",
      "method_name": "方法2",
      "count": 32,
      "ratio": 0.25,
      "percentage": 25.0
    },
    {
      "method": "Method_m8vwGkEZc3TSW2xqYUoR",
      "method_name": "方法3",
      "count": 28,
      "ratio": 0.22,
      "percentage": 22.0
    },
    {
      "method": "Method_5Q4KoXthUuYz3bvrTDFm",
      "method_name": "方法4",
      "count": 15,
      "ratio": 0.12,
      "percentage": 12.0
    },
    {
      "method": "Method_other",
      "method_name": "其他",
      "count": 8,
      "ratio": 0.06,
      "percentage": 6.0
    }
  ],
  "total_methods": 5
}
```

---

### 5. 获取知识点掌握情况（蓝色框1 - Tab 4: 知识点）

**接口地址：** `GET /api/learning-profile/knowledge-mastery`

**请求参数：**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| student_id | string | 否 | 学习者ID，不传则返回群体数据 |
| class_name | string | 否 | 班级名称，用于群体分析 |
| month | string | 否 | 月份筛选（格式：YYYY-MM） |

**响应示例：**
```json
{
  "knowledge_stats": [
    {
      "knowledge_id": "r8S3g",
      "knowledge_name": "知识点1",
      "mastery": 0.75,
      "mastery_percentage": 75.0,
      "question_count": 12,
      "submit_count": 45,
      "correct_count": 34,
      "level": "good"
    },
    {
      "knowledge_id": "k9T4h",
      "knowledge_name": "知识点2",
      "mastery": 0.55,
      "mastery_percentage": 55.0,
      "question_count": 8,
      "submit_count": 28,
      "correct_count": 15,
      "level": "medium"
    },
    {
      "knowledge_id": "m5V6w",
      "knowledge_name": "知识点3",
      "mastery": 0.35,
      "mastery_percentage": 35.0,
      "question_count": 15,
      "submit_count": 52,
      "correct_count": 18,
      "level": "poor"
    }
  ],
  "summary": {
    "total_knowledge": 3,
    "good_count": 1,
    "medium_count": 1,
    "poor_count": 1
  }
}
```

**level说明：**
- `good`: mastery >= 0.6 (绿色)
- `medium`: 0.4 <= mastery < 0.6 (橙色)
- `poor`: mastery < 0.4 (红色)

---

### 6. 获取24小时答题高峰时段（蓝色框2 - 上半部分）

**接口地址：** `GET /api/learning-profile/hour-distribution`

**请求参数：**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| student_id | string | 否 | 学习者ID，不传则返回群体数据 |
| class_name | string | 否 | 班级名称，用于群体分析 |
| month | string | 否 | 月份筛选（格式：YYYY-MM），不传则返回所有月份聚合数据 |

**响应示例：**
```json
{
  "hour_distribution": [
    {"hour": 0, "count": 2, "percentage": 0.5},
    {"hour": 1, "count": 0, "percentage": 0.0},
    {"hour": 2, "count": 1, "percentage": 0.25},
    ...
    {"hour": 9, "count": 45, "percentage": 11.25},
    {"hour": 10, "count": 52, "percentage": 13.0},
    {"hour": 11, "count": 48, "percentage": 12.0},
    {"hour": 12, "count": 38, "percentage": 9.5},
    ...
    {"hour": 23, "count": 5, "percentage": 1.25}
  ],
  "peak_hours": [10, 11, 14, 15, 16],
  "total_count": 400
}
```

**字段说明：**
- `hour`: 小时值（0-23）
- `count`: 该时段的提交次数
- `percentage`: 该时段占总提交次数的百分比
- `peak_hours`: 高峰时段列表（提交次数最多的前5个时段）

---

### 7. 获取月度活动热力图数据（蓝色框2 - 下半部分）

**接口地址：** `GET /api/learning-profile/monthly-heatmap`

**请求参数：**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| student_id | string | 否 | 学习者ID，不传则返回群体数据 |
| class_name | string | 否 | 班级名称，用于群体分析 |
| start_month | string | 否 | 起始月份（格式：YYYY-MM），默认最近3个月 |
| end_month | string | 否 | 结束月份（格式：YYYY-MM），默认当前月份 |

**响应示例：**
```json
{
  "heatmap_data": [
    {
      "month": "2024-10",
      "month_name": "10月",
      "days": [
        {"day": 1, "count": 5, "level": "low"},
        {"day": 2, "count": 0, "level": "none"},
        {"day": 3, "count": 12, "level": "medium"},
        ...
        {"day": 31, "count": 8, "level": "low"}
      ]
    },
    {
      "month": "2024-11",
      "month_name": "11月",
      "days": [
        {"day": 1, "count": 15, "level": "medium"},
        {"day": 2, "count": 22, "level": "high"},
        ...
        {"day": 30, "count": 18, "level": "medium"}
      ]
    },
    {
      "month": "2024-12",
      "month_name": "12月",
      "days": [
        {"day": 1, "count": 10, "level": "low"},
        ...
      ]
    }
  ],
  "summary": {
    "total_days": 92,
    "active_days": 45,
    "max_count": 25,
    "min_count": 0
  }
}
```

**level说明：**
- `none`: count = 0
- `low`: 0 < count <= 5
- `medium`: 5 < count <= 15
- `high`: count > 15

---

### 8. 获取综合数据（蓝色框1 - 所有Tab数据一次性获取）

**接口地址：** `GET /api/learning-profile/comprehensive-bluebox1`

**请求参数：**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| student_id | string | 否 | 学习者ID，不传则返回群体数据 |
| class_name | string | 否 | 班级名称，用于群体分析 |
| month | string | 否 | 月份筛选（格式：YYYY-MM） |

**响应示例：**
```json
{
  "tab1_basic_features": {
    "submit_count": 156,
    "active_days": 23,
    "question_count": 45,
    "correct_ratio": 0.85,
    "pattern": "探索尝试型",
    "comparison": {
      "submit_count_avg": 120,
      "active_days_avg": 18,
      "question_count_avg": 35,
      "correct_ratio_avg": 0.78
    }
  },
  "tab2_pattern_distribution": {
    "patterns": {
      "探索尝试型": 15,
      "广泛多样型": 8,
      "集中针对型": 12
    },
    "total": 35
  },
  "tab3_method_preference": {
    "method_distribution": [
      {"method": "Method_xxx", "count": 45, "ratio": 0.35},
      ...
    ]
  },
  "tab4_knowledge_mastery": {
    "knowledge_stats": [
      {"knowledge_id": "r8S3g", "mastery": 0.75, "level": "good"},
      ...
    ]
  }
}
```

---

### 9. 获取蓝色框2综合数据

**接口地址：** `GET /api/learning-profile/comprehensive-bluebox2`

**请求参数：**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| student_id | string | 否 | 学习者ID，不传则返回群体数据 |
| class_name | string | 否 | 班级名称，用于群体分析 |
| month | string | 否 | 月份筛选（格式：YYYY-MM） |

**响应示例：**
```json
{
  "hour_distribution": {
    "hour_distribution": [
      {"hour": 0, "count": 2},
      ...
    ],
    "peak_hours": [10, 11, 14, 15, 16]
  },
  "monthly_heatmap": {
    "heatmap_data": [
      {
        "month": "2024-10",
        "month_name": "10月",
        "days": [
          {"day": 1, "count": 5, "level": "low"},
          ...
        ]
      },
      ...
    ]
  }
}
```

---

## 筛选条件组合说明

### 筛选逻辑

1. **优先级规则：**
   - 如果同时提供 `student_id` 和 `class_name`，优先使用 `student_id`（个体分析）
   - 如果只提供 `class_name`，返回该班级的群体数据
   - 如果只提供 `student_id`，返回该学生的个体数据

2. **月份筛选：**
   - 提供 `month` 参数：返回指定月份的数据
   - 不提供 `month` 参数：返回所有月份的聚合数据（用于总体趋势分析）

3. **筛选条件组合示例：**
   - `class_name=J23517` + `month=2024-01`: 获取J23517班级在2024年1月的数据
   - `student_id=xxx` + `month=2024-02`: 获取某学生在2024年2月的数据
   - `class_name=J23517`（无month）: 获取J23517班级所有月份的聚合数据
   - `student_id=xxx`（无month）: 获取某学生所有月份的聚合数据

---

## 数据格式说明

### 学习模式分类规则

1. **探索尝试型**：submit_ratio >= 0.85 AND correct_ratio >= 0.85
2. **广泛多样型**：question_ratio >= 0.85 AND correct_ratio < 0.85 AND active_ratio >= 0.8
3. **集中针对型**：其他情况

### 特征计算说明

- **submit_count**: 有效提交记录总数
- **active_days**: 有提交记录的不重复日期数
- **question_count**: 答题的不同题目编号数
- **correct_ratio**: 状态为'Absolutely_Correct'或'Partially_Correct'的记录占比

---

## 错误处理

所有接口在出错时应返回以下格式：

```json
{
  "error": "错误信息描述",
  "code": "ERROR_CODE"
}
```

**常见错误码：**
- `INVALID_PARAMETER`: 参数错误
- `DATA_NOT_FOUND`: 数据未找到
- `SERVER_ERROR`: 服务器内部错误

---

## 接口使用示例

### 示例1：获取某学生2024年1月的基础特征（Tab 1）
```
GET /api/learning-profile/behavior-features?student_id=8b6d1125760bd3939b6e&month=2024-01
```

### 示例2：获取某班级的学习模式分布（Tab 2）
```
GET /api/learning-profile/pattern-distribution?class_name=J23517&month=2024-01
```

### 示例3：获取某学生的编程方法偏好（Tab 3）
```
GET /api/learning-profile/method-preference?student_id=8b6d1125760bd3939b6e&month=2024-01
```

### 示例4：获取某学生的知识点掌握情况（Tab 4）
```
GET /api/learning-profile/knowledge-mastery?student_id=8b6d1125760bd3939b6e&month=2024-01
```

### 示例5：获取蓝色框1所有Tab数据（一次性获取）
```
GET /api/learning-profile/comprehensive-bluebox1?student_id=8b6d1125760bd3939b6e&month=2024-01
```

### 示例6：获取蓝色框2数据（24小时分布 + 月度热力图）
```
GET /api/learning-profile/comprehensive-bluebox2?student_id=8b6d1125760bd3939b6e&month=2024-01
```

### 示例7：获取可用月份列表
```
GET /api/learning-profile/available-months?student_id=8b6d1125760bd3939b6e
```

---

## 前端实现建议

1. **蓝色框1：**
   - 顶部：月份选择器 + 筛选按钮 + 重置按钮
   - Tab切换：基础特征、学习模式、编程方法、知识点（左右平滑切换）
   - 内容区：根据选中的Tab显示对应的图表

2. **蓝色框2：**
   - 上半部分：24小时答题高峰时段（径向气泡图）
   - 下半部分：月度活动热力图

3. **筛选联动：**
   - 月份选择器与顶部的class/student选择器联动
   - 点击筛选按钮时，使用当前的class/student/month组合作为筛选条件
   - 点击重置按钮时，清空月份选择，使用class/student的所有月份聚合数据

