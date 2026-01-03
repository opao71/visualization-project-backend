# 5.4.1 green_topViews.py 后端实现文档

## (一) 数据加载与预处理

### 1. 数据文件路径配置

模块定义了统一的数据文件路径常量，包括：

- **基础路径**：`BASE_DIR`、`DATA_DIR`、`MASTER_DIR`、`SUBMIT_DIR`
- **数据文件**：
  - `TITLE_INFO_FILE`：题目信息文件（Data_TitleInfo.csv）
  - `STUDENT_INFO_FILE`：学生信息文件（Data_StudentInfo.csv）
  - `INDIVIDUAL_TITLE_FILE`：个人题目掌握度文件
  - `INDIVIDUAL_KNOWLEDGE_FILE`：个人知识点掌握度文件
  - `MAJOR_KNOWLEDGE_FILE`：专业知识点掌握度文件

### 2. 数据标准化处理

#### (1) `_normalize_columns(df: pd.DataFrame) -> pd.DataFrame`
- **功能**：标准化DataFrame列名，去除BOM字符和前后空格
- **处理逻辑**：
  - 将列名转换为字符串类型
  - 去除BOM字符（`\ufeff`）
  - 去除列名前后的空格
- **应用场景**：处理CSV文件读取时可能出现的编码和格式问题

#### (2) `_normalize_column_name(df: pd.DataFrame, target: str) -> pd.DataFrame`
- **功能**：标准化特定列名（大小写不敏感匹配）
- **处理逻辑**：
  - 检查目标列名是否已存在
  - 如果不存在，进行大小写不敏感匹配
  - 找到匹配的列名后重命名
- **应用场景**：处理列名大小写不一致的情况

### 3. 数据加载函数（带缓存）

所有数据加载函数均使用 `@lru_cache(maxsize=1)` 装饰器实现内存缓存，避免重复读取文件。

#### (1) `load_title_info() -> pd.DataFrame`
- **功能**：加载题目信息数据
- **返回字段**：`title_ID`、`knowledge`、`sub_knowledge`、`score`
- **处理**：去除重复记录，标准化列名

#### (2) `load_student_info() -> pd.DataFrame`
- **功能**：加载学生基本信息
- **返回字段**：`student_ID`、`major`
- **处理**：去除重复记录，标准化列名

#### (3) `load_submit_records() -> pd.DataFrame`
- **功能**：加载所有提交记录（合并多个CSV文件）
- **处理逻辑**：
  - 使用 `glob.glob()` 查找所有 `SubmitRecord-Class*.csv` 文件
  - 逐个读取并标准化列名
  - 合并所有DataFrame
- **返回字段**：`student_ID`、`title_ID`、`class`、`state`、`score`
- **容错处理**：如果文件不存在或字段缺失，返回空DataFrame

#### (4) `load_individual_knowledge_mastery() -> pd.DataFrame`
- **功能**：加载个人知识点掌握度数据
- **返回字段**：`student_ID`、`knowledge`、`knowledge_mastery_score`

#### (5) `load_individual_title_mastery() -> pd.DataFrame`
- **功能**：加载个人题目掌握度数据
- **返回字段**：包含学生ID、题目ID和掌握度分数

#### (6) `load_major_knowledge_mastery() -> pd.DataFrame`
- **功能**：加载专业知识点掌握度数据
- **返回字段**：`major`、`knowledge`、`knowledge_mastery_score`

## (二) 学习模式分类

### 1. 学习模式类型定义

系统将学生学习模式分为四种类型：

- **反复练习型**：重复提交率 > 3（同一题目多次提交）
- **探索尝试型**：尝试题目数量 > 30（广泛尝试不同题目）
- **稳步推进型**：其他情况（介于两者之间）
- **未知型**：无提交记录的学生

### 2. 学习模式判断函数

#### (1) `get_student_learning_pattern(student_id: str, submit_records: pd.DataFrame, title_info: pd.DataFrame) -> str`
- **功能**：判断单个学生的学习模式
- **计算指标**：
  - `unique_titles`：尝试的题目数量
  - `total_submits`：总提交次数
  - `repeat_rate`：重复提交率 = 总提交次数 / 唯一题目数
- **判断逻辑**：
  - 如果 `repeat_rate > 3` → 反复练习型
  - 如果 `unique_titles > 30` → 探索尝试型
  - 否则 → 稳步推进型

#### (2) `batch_calculate_learning_patterns(student_ids: List[str], submit_records: pd.DataFrame) -> Dict[str, str]`
- **功能**：批量计算学生学习模式（性能优化版本）
- **优化策略**：
  - 使用 `groupby` 一次性计算所有学生的统计信息
  - 避免循环中重复查询DataFrame
- **返回**：学生ID到学习模式的字典映射

### 3. 学生抽样策略

#### (1) `stratified_sample_students(major: str, student_info: pd.DataFrame, submit_records: pd.DataFrame, title_info: pd.DataFrame, sample_size: int = 15) -> List[str]`
- **功能**：按专业+学习模式分层抽样代表性学生
- **抽样策略**：
  - 按学习模式分组
  - 按比例从每组中抽样
  - 确保每组至少抽取1个学生
  - 如果未达到目标数量，随机补充
- **应用场景**：需要展示专业代表性学生时使用

#### (2) `get_unique_pattern_students(major: str, student_info: pd.DataFrame, submit_records: pd.DataFrame, title_info: pd.DataFrame, student_patterns: Dict[str, str]) -> List[str]`
- **功能**：获取每个专业-学习模式组合的唯一代表性学生
- **抽样策略**：
  - 按学习模式分组
  - 每个学习模式只选择一个代表性学生
  - 使用预计算的学习模式字典（避免重复计算）
- **应用场景**：桑基图中每个专业-学习模式组合只显示一个学生节点

## (三) API接口实现

### (1) 获取桑基图数据接口

**接口路径**：`GET /api/green/top/sankey`

**功能描述**：构建并返回桑基图所需的所有节点和链路数据，展示从知识点到专业、从专业到学生、从学生到题目的学习路径分布。

**实现函数**：`build_sankey_data() -> Dict[str, Any]`

#### 数据结构设计

返回数据包含两个主要部分：

```json
{
  "nodes": [...],  // 节点数组
  "links": [...]   // 链路数组
}
```

#### 节点类型（category字段）

- **category 0**：主知识点节点
  - 包含：知识点名称、平均掌握度、关联题目数、总分值
- **category 1**：专业群体节点
  - 包含：专业名称、专业类别、专业人数、平均掌握度、提交总量
- **category 2**：学生个体节点
  - 包含：专业、学习模式、个人综合掌握度、正确率、总提交次数
- **category 3**：题目节点
  - 包含：所属知识点、题目分值、综合效率

#### 链路类型

1. **正向链路**：
   - 知识点 → 专业：表示专业对知识点的学习投入（提交量）
   - 专业 → 学生：表示学生属于该专业（固定值1）
   - 学生 → 题目：表示学生对题目的提交次数

2. **反向链路**：
   - 题目 → 学生：反向关联，便于可视化交互
   - 学生 → 专业：反向关联
   - 专业 → 知识点：反向关联

#### 核心计算逻辑

1. **知识点节点构建**：
   - 遍历所有知识点
   - 计算每个知识点的题目总量和总分值
   - 计算所有学生在该知识点的平均掌握度
   - 按预定义顺序排序（避免字体重叠）

2. **专业节点构建**：
   - 遍历所有专业
   - 计算专业人数、平均掌握度、提交总量
   - 添加专业名称和类别信息

3. **学生节点构建**：
   - 使用 `get_unique_pattern_students()` 获取代表性学生
   - 批量计算学生统计信息（掌握度、正确率、提交次数）
   - 为每个学生创建节点

4. **题目节点构建**：
   - 遍历所有题目
   - 计算题目的综合效率（平均掌握度）
   - 关联到对应的知识点

5. **链路构建**：
   - 知识点→专业：计算专业对知识点相关题目的提交量
   - 专业→学生：建立专业与学生的关联
   - 学生→题目：统计学生对每个题目的提交次数和正确率
   - 反向链路：建立反向关联，增强可视化交互性

#### 性能优化

1. **批量计算**：
   - 使用 `batch_calculate_learning_patterns()` 批量计算学习模式
   - 使用 `batch_calculate_student_stats()` 批量计算学生统计信息

2. **数据缓存**：
   - 所有数据加载函数使用 `@lru_cache` 装饰器
   - 避免重复读取文件

3. **预计算**：
   - 预先计算所有学生的学习模式
   - 预先计算所有抽样学生的统计信息

#### 错误处理

- 使用 try-except 捕获异常
- 返回错误信息：`{'error': str(exc)}`
- HTTP状态码：500（服务器错误）

## (四) 数据缓存机制

### 1. LRU缓存装饰器

所有数据加载函数使用 `@lru_cache(maxsize=1)` 装饰器：

- **缓存策略**：最近最少使用（LRU）
- **缓存大小**：`maxsize=1`（只缓存最新一次的结果）
- **优势**：
  - 避免重复读取文件
  - 提高API响应速度
  - 减少I/O操作

### 2. 缓存函数列表

- `load_title_info()`
- `load_student_info()`
- `load_submit_records()`
- `load_individual_knowledge_mastery()`
- `load_individual_title_mastery()`
- `load_major_knowledge_mastery()`

### 3. 缓存失效

- 缓存会在Python进程重启时自动清除
- 如果需要强制刷新缓存，需要重启后端服务

## (五) 错误处理机制

### 1. API路由错误处理

```python
@green_top_bp.route('/sankey', methods=['GET'])
def get_sankey():
    try:
        data = build_sankey_data()
        return jsonify(data)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500
```

- **捕获范围**：捕获所有异常
- **错误响应**：返回JSON格式的错误信息
- **HTTP状态码**：500（服务器内部错误）

### 2. 数据加载容错处理

- **文件不存在**：返回空DataFrame，避免程序崩溃
- **列名缺失**：使用 `_normalize_column_name()` 进行容错匹配
- **编码问题**：使用 `encoding='utf-8-sig'` 处理BOM字符

### 3. 数据验证

- **空数据检查**：在关键计算前检查DataFrame是否为空
- **字段存在性检查**：使用 `if 'column' in df.columns` 检查字段是否存在
- **默认值处理**：为缺失数据提供合理的默认值（如0.0、空列表等）

## (六) 辅助功能函数

### 1. 名称映射函数

#### (1) `get_major_name(major_code: str) -> str`
- **功能**：将专业编号转换为专业名称
- **映射表**：
  - `J78901` → 计算机科学与技术
  - `J87654` → 软件工程
  - `J23517` → 数据科学与大数据技术
  - `J40192` → 人工智能
  - `J57489` → 网络工程
- **容错**：如果编号不在映射表中，返回格式化的名称

#### (2) `get_major_category(major_code: str) -> str`
- **功能**：获取专业类别（用于颜色映射）
- **分类**：计算机类、数据类、人工智能类、网络类、其他类

#### (3) `get_knowledge_name(knowledge_code: str) -> str`
- **功能**：将知识点编码转换为知识点名称
- **映射表**：
  - `r8S3g` → 程序控制
  - `m3D1v` → 数据结构
  - `b3C9s` → 基础语法
  - `g7R2j` → 函数与模块
  - `k4W1c` → 异常处理
  - `s8Y2f` → 文件操作
  - `t5V9e` → 算法设计
  - `y9W5d` → 面向对象

### 2. 学生统计计算函数

#### (1) `calculate_student_overall_mastery(student_id: str, individual_knowledge: pd.DataFrame) -> float`
- **功能**：计算学生个人综合掌握度
- **计算方式**：所有知识点掌握度的平均值 × 100
- **返回**：0-100之间的浮点数

#### (2) `calculate_student_accuracy(student_id: str, submit_records: pd.DataFrame) -> Dict[str, Any]`
- **功能**：计算学生正确率和总提交次数
- **返回字段**：
  - `accuracy`：正确率（百分比）
  - `total_submits`：总提交次数
- **计算逻辑**：正确提交数 / 总提交数 × 100

#### (3) `batch_calculate_student_stats(student_ids: List[str], individual_knowledge: pd.DataFrame, submit_records: pd.DataFrame) -> Dict[str, Dict[str, Any]]`
- **功能**：批量计算学生统计信息（性能优化版本）
- **优化策略**：
  - 使用 `groupby` 批量计算掌握度
  - 使用 `groupby` 批量计算准确率和提交次数
  - 避免循环中重复查询
- **返回**：学生ID到统计信息的字典映射
- **统计信息包含**：
  - `overall_mastery`：综合掌握度
  - `accuracy`：正确率
  - `total_submits`：总提交次数

## (七) 技术特点总结

### 1. 性能优化

- **数据缓存**：使用LRU缓存避免重复读取文件
- **批量计算**：使用pandas的groupby进行批量操作，避免循环
- **预计算**：预先计算学习模式和统计信息，减少重复计算

### 2. 代码质量

- **类型提示**：使用类型注解提高代码可读性
- **函数封装**：将复杂逻辑拆分为多个小函数
- **容错处理**：完善的错误处理和默认值设置

### 3. 可维护性

- **模块化设计**：功能清晰分离，易于维护和扩展
- **注释完善**：关键函数都有详细的文档字符串
- **命名规范**：函数和变量命名清晰，符合Python规范

### 4. 数据完整性

- **数据验证**：在关键步骤进行数据验证
- **空值处理**：妥善处理空数据和缺失字段
- **编码处理**：正确处理CSV文件的编码问题

