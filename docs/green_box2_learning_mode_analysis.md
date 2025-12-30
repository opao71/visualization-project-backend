# Green Box 2 - 学习模式分析 API 接口文档

## 概述

本文档定义了绿色框2（学习模式分析）所需的API接口。该接口用于支持4个散点图的可视化展示，分析知识掌握程度与学习时长、编程习惯、平均得分、提交次数之间的关系。

---

## 接口说明

### 获取学习模式分析数据

**接口地址：** `GET /api/green/box2/learning-mode-analysis`

**请求参数：**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| class | string | 否 | 班级名称，例如 `Class1`。如果提供，返回该班级所有学生的数据 |
| student_ID | string | 否 | 学生唯一ID。如果提供，返回该学生的数据 |
| month | string | 否 | 月份筛选（格式：YYYY-MM），不传则返回所有月份聚合数据 |

**说明：**
- 如果同时提供 `class` 和 `student_ID`，优先使用 `student_ID`（返回单个学生的数据）
- 如果只提供 `class`，返回该班级所有学生的数据（用于班级整体分析）
- 如果只提供 `student_ID`，返回该学生的数据
- 如果都不提供，返回所有学生的数据（用于全局分析）
- `month` 参数用于时间维度筛选，支持按月份查看不同时期的学习模式

**响应示例：**
```json
{
  "class": "Class1",
  "student": null,
  "month": null,
  "scatter_plots": {
    "learning_duration": {
      "title": "知识掌握程度 vs 学习时长",
      "x_axis_label": "学习时长",
      "y_axis_label": "知识掌握程度(%)",
      "data": [
        {
          "student_ID": "8b6d1125760bd3939b6e",
          "x_value": 125.5,
          "y_value": 45.2,
          "student_name": "学生A"
        },
        {
          "student_ID": "63eef37311aaac915a45",
          "x_value": 89.3,
          "y_value": 38.7,
          "student_name": "学生B"
        }
      ],
      "statistics": {
        "x_min": 0,
        "x_max": 500,
        "y_min": 0,
        "y_max": 80,
        "correlation": 0.15,
        "data_count": 35
      }
    },
    "coding_habits": {
      "title": "知识掌握程度 vs 编程习惯",
      "x_axis_label": "编程习惯",
      "y_axis_label": "知识掌握程度(%)",
      "data": [
        {
          "student_ID": "8b6d1125760bd3939b6e",
          "x_value": 0.85,
          "y_value": 45.2,
          "student_name": "学生A"
        },
        {
          "student_ID": "63eef37311aaac915a45",
          "x_value": 0.62,
          "y_value": 38.7,
          "student_name": "学生B"
        }
      ],
      "statistics": {
        "x_min": 0,
        "x_max": 1,
        "y_min": 0,
        "y_max": 80,
        "correlation": 0.72,
        "data_count": 35
      }
    },
    "average_score": {
      "title": "知识掌握程度 vs 平均得分",
      "x_axis_label": "平均得分",
      "y_axis_label": "知识掌握程度(%)",
      "data": [
        {
          "student_ID": "8b6d1125760bd3939b6e",
          "x_value": 2.8,
          "y_value": 45.2,
          "student_name": "学生A"
        },
        {
          "student_ID": "63eef37311aaac915a45",
          "x_value": 1.5,
          "y_value": 38.7,
          "student_name": "学生B"
        }
      ],
      "statistics": {
        "x_min": 0,
        "x_max": 4,
        "y_min": 0,
        "y_max": 80,
        "correlation": 0.68,
        "data_count": 35
      }
    },
    "submit_count": {
      "title": "知识掌握程度 vs 提交次数",
      "x_axis_label": "提交次数",
      "y_axis_label": "知识掌握程度(%)",
      "data": [
        {
          "student_ID": "8b6d1125760bd3939b6e",
          "x_value": 67,
          "y_value": 45.2,
          "student_name": "学生A"
        },
        {
          "student_ID": "63eef37311aaac915a45",
          "x_value": 246,
          "y_value": 38.7,
          "student_name": "学生B"
        }
      ],
      "statistics": {
        "x_min": 0,
        "x_max": 500,
        "y_min": 0,
        "y_max": 80,
        "correlation": -0.12,
        "data_count": 35
      }
    }
  }
}
```

**字段说明：**

#### scatter_plots 对象
包含4个散点图的数据，每个散点图包含以下字段：

- `title`: 图表标题
- `x_axis_label`: X轴标签
- `y_axis_label`: Y轴标签（统一为"知识掌握程度(%)"）
- `data`: 散点数据数组，每个元素包含：
  - `student_ID`: 学生唯一ID
  - `x_value`: X轴数值（根据图表类型不同，含义不同）
  - `y_value`: Y轴数值（知识掌握程度，0-80%）
  - `student_name`: 学生名称（可选，如果数据源中有）
- `statistics`: 统计信息
  - `x_min`, `x_max`: X轴数值范围
  - `y_min`, `y_max`: Y轴数值范围（y_max固定为80）
  - `correlation`: 相关系数（-1到1之间，用于分析相关性）
  - `data_count`: 数据点数量

#### 各散点图的X轴含义

1. **learning_duration（学习时长）**
   - `x_value`: 学习总时长（小时）
   - 计算方式：从提交记录中计算每个学生的总学习时长
   - 可以基于 `timeconsume` 字段累加，或基于时间跨度计算

2. **coding_habits（编程习惯）**
   - `x_value`: 编程习惯得分（0-1之间的浮点数）
   - 计算方式：基于方法使用的一致性、多样性等指标综合计算
   - 可以考虑的因素：
     - 方法使用的一致性（同一题目使用相同方法的比例）
     - 方法使用的多样性（使用不同方法的数量）
     - 方法选择的合理性（正确率与方法的关联）

3. **average_score（平均得分）**
   - `x_value`: 平均得分（0-4之间的浮点数）
   - 计算方式：所有提交记录的平均 `score` 值

4. **submit_count（提交次数）**
   - `x_value`: 提交次数（整数）
   - 计算方式：有效提交记录的总数

#### Y轴（知识掌握程度）计算方式

- 从 `mastery/individual_knowledge_mastery.csv` 或 `learning_behavior/student_knowledge_mastery.csv` 中获取
- 计算每个学生的平均知识掌握程度（所有知识点的平均值）
- 转换为百分比（0-80%），超出80%的按80%处理

---

## 数据来源 & 预处理

| 文件 | 作用 |
|------|------|
| `Data_SubmitRecord/SubmitRecord-Class*.csv` | 获取提交记录，计算学习时长、平均得分、提交次数、编程习惯 |
| `mastery/individual_knowledge_mastery.csv` | 获取知识点掌握度，计算平均知识掌握程度 |
| `learning_behavior/student_knowledge_mastery.csv` | 备选：获取学生知识点掌握度 |
| `Data_StudentInfo.csv` | 获取学生信息（如需要学生名称） |

---

## 筛选逻辑

### 1. 班级/学生筛选
- 如果提供 `class`，从对应的 `SubmitRecord-Class*.csv` 中筛选该班级的学生
- 如果提供 `student_ID`，只返回该学生的数据
- 如果同时提供，优先使用 `student_ID`

### 2. 月份筛选
- 如果提供 `month`，只统计该月份的提交记录
- 如果不提供，统计所有月份的聚合数据
- 月份格式：`YYYY-MM`（例如：`2024-01`）

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
- `INVALID_PARAMETER`: 参数错误（如月份格式不正确）
- `DATA_NOT_FOUND`: 数据未找到（如班级或学生不存在）
- `SERVER_ERROR`: 服务器内部错误

---

## 接口使用示例

### 示例1：获取某班级的学习模式分析
```
GET /api/green/box2/learning-mode-analysis?class=Class1
```

### 示例2：获取某学生的学习模式分析
```
GET /api/green/box2/learning-mode-analysis?student_ID=8b6d1125760bd3939b6e
```

### 示例3：获取某班级在指定月份的学习模式分析
```
GET /api/green/box2/learning-mode-analysis?class=Class1&month=2024-01
```

### 示例4：获取所有学生的学习模式分析（全局视图）
```
GET /api/green/box2/learning-mode-analysis
```

---

## 前端提示

### 图表配置建议

1. **散点图配置**
   - 使用 ECharts 的 `scatter` 类型
   - Y轴范围固定为 0-80
   - X轴范围根据 `statistics` 中的 `x_min` 和 `x_max` 动态设置
   - 可以添加趋势线显示相关性

2. **交互功能**
   - 鼠标悬停显示学生ID和具体数值
   - 点击散点可以跳转到学生详情（如果前端支持）
   - 支持缩放和平移查看数据细节

3. **视觉设计**
   - 4个散点图使用不同的颜色主题区分
   - 高密度区域可以使用颜色深浅表示数据点密度
   - 参考图片中的橙色高亮区域，可以添加密度热力图效果

---

## 数据计算细节

### 学习时长计算
```python
# 方案1：基于timeconsume累加（秒转小时）
learning_duration = sum(timeconsume) / 3600

# 方案2：基于时间跨度
first_submit = min(time)
last_submit = max(time)
learning_duration = (last_submit - first_submit) / 3600 / 24  # 天数转小时
```

### 编程习惯计算
```python
# 计算指标
method_consistency = 同一题目使用相同方法的比例
method_diversity = 使用不同方法的数量 / 总题目数
method_effectiveness = 正确率与方法的关联度

# 综合得分（示例公式，可根据实际需求调整）
coding_habits_score = (
    method_consistency * 0.4 + 
    method_diversity * 0.3 + 
    method_effectiveness * 0.3
)
```

### 知识掌握程度计算
```python
# 从知识点掌握度数据中获取
knowledge_mastery_df = load_individual_knowledge_mastery()
student_mastery = knowledge_mastery_df[
    knowledge_mastery_df['student_ID'] == student_id
]['knowledge_mastery_score'].mean()

# 转换为百分比并限制在0-80
mastery_percentage = min(student_mastery * 100, 80)
```

---

## 注意事项

1. **数据完整性**：如果某个学生缺少知识点掌握数据，该学生的数据点可能不包含在结果中
2. **性能优化**：对于班级级别的查询，建议后端进行数据缓存
3. **相关性分析**：`correlation` 字段可以帮助前端判断数据趋势，正值表示正相关，负值表示负相关
4. **数据范围**：Y轴固定为0-80%，超出范围的数据会被截断，但原始数据应保留在 `y_value` 中

