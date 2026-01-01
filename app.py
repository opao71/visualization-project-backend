from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import pandas as pd
import os
import json
from datetime import datetime
from typing import Optional

from pink_views import pink_bp
from green_topViews import green_top_bp
from green_box2_views import green_box2_bp
from learning_behavior import LearningBehaviorAnalyzer
from learner_profile import LearnerProfileAnalyzer

app = Flask(__name__)
CORS(app)
app.register_blueprint(pink_bp)
app.register_blueprint(green_top_bp)
app.register_blueprint(green_box2_bp)

# 数据文件路径
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
STUDENT_INFO_FILE = os.path.join(DATA_DIR, 'Data_StudentInfo.csv')
CLASS_TITLE_MASTERY = os.path.join(DATA_DIR, 'mastery', 'class_title_mastery.csv')
INDIVIDUAL_TITLE_MASTERY = os.path.join(DATA_DIR, 'mastery', 'individual_title_mastery.csv')
CLASS_KNOWLEDGE_MASTERY = os.path.join(DATA_DIR, 'mastery', 'class_knowledge_mastery.csv')
INDIVIDUAL_KNOWLEDGE_MASTERY = os.path.join(DATA_DIR, 'mastery', 'individual_knowledge_mastery.csv')
INDIVIDUAL_SUB_KNOWLEDGE_MASTERY = os.path.join(DATA_DIR, 'mastery', 'individual_sub_knowledge_mastery.csv')
MAJOR_KNOWLEDGE_MASTERY = os.path.join(DATA_DIR, 'mastery', 'major_knowledge_mastery.csv')
MAJOR_TITLE_MASTERY = os.path.join(DATA_DIR, 'mastery', 'major_title_mastery.csv')

def safe_json_loads(raw: str):
    """解析 query 中 data 字符串，确保返回 dict。"""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def build_class_summary(selected_class: Optional[str] = None):
    df = pd.read_csv(CLASS_TITLE_MASTERY)
    summary_df = (
        df.groupby('class')['title_mastery_score']
        .mean()
        .reset_index()
        .rename(columns={'title_mastery_score': 'avg_mastery'})
        .sort_values('class')
    )
    summary = summary_df.to_dict('records')

    details = []
    if selected_class:
        class_df = (
            df[df['class'] == selected_class][['title_ID', 'score_rate', 'average_tc',
                                               'average_memory', 'title_mastery_score']]
            .sort_values('title_mastery_score', ascending=False)
            .head(50)
        )
        details = class_df.to_dict('records')

    available = sorted(df['class'].unique().tolist())
    return summary, details, available


def build_student_mastery(student_id: Optional[str] = None):
    df = pd.read_csv(INDIVIDUAL_TITLE_MASTERY)
    summary = []
    if student_id:
        summary_df = (
            df[df['student_ID'] == student_id][['title_ID', 'score_rate', 'average_tc',
                                                'average_memory', 'title_mastery_score']]
            .sort_values('title_mastery_score', ascending=False)
            .head(50)
        )
        summary = summary_df.to_dict('records')
    available = sorted(df['student_ID'].unique().tolist())
    return summary, available


def build_knowledge_snapshot(class_name: Optional[str] = None, student_id: Optional[str] = None):
    class_df = pd.read_csv(CLASS_KNOWLEDGE_MASTERY)
    class_snapshot = class_df.to_dict('records')
    if class_name:
        class_snapshot = class_df[class_df['class'] == class_name].to_dict('records')

    indiv_df = pd.read_csv(INDIVIDUAL_KNOWLEDGE_MASTERY)
    individual_snapshot = []
    if student_id:
        individual_snapshot = indiv_df[indiv_df['student_ID'] == student_id].to_dict('records')

    sub_df = pd.read_csv(INDIVIDUAL_SUB_KNOWLEDGE_MASTERY)
    sub_snapshot = []
    if student_id:
        sub_snapshot = sub_df[sub_df['student_ID'] == student_id].to_dict('records')

    major_k_df = pd.read_csv(MAJOR_KNOWLEDGE_MASTERY)
    major_t_df = pd.read_csv(MAJOR_TITLE_MASTERY)

    return {
        'classKnowledge': class_snapshot[:50],
        'individualKnowledge': individual_snapshot[:50],
        'individualSubKnowledge': sub_snapshot[:50],
        'majorKnowledge': major_k_df.to_dict('records')[:50],
        'majorTitle': major_t_df.to_dict('records')[:50],
    }

# 处理后的数据文件路径
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'learning_behavior')
STUDENT_BEHAVIOR_FEATURES = os.path.join(PROCESSED_DATA_DIR, 'student_behavior_features.csv')
CLASS_PATTERN_DISTRIBUTION = os.path.join(PROCESSED_DATA_DIR, 'class_pattern_distribution.csv')
STUDENT_HOUR_DISTRIBUTION = os.path.join(PROCESSED_DATA_DIR, 'student_hour_distribution.csv')
STUDENT_METHOD_PREFERENCE = os.path.join(PROCESSED_DATA_DIR, 'student_method_preference.csv')
STUDENT_KNOWLEDGE_MASTERY = os.path.join(PROCESSED_DATA_DIR, 'student_knowledge_mastery.csv')
STUDENT_MONTHLY_STATS = os.path.join(PROCESSED_DATA_DIR, 'student_monthly_stats.csv')
MONTHLY_BEHAVIOR_FEATURES = os.path.join(PROCESSED_DATA_DIR, 'monthly_behavior_features.csv')
CLASS_HOUR_DISTRIBUTION = os.path.join(PROCESSED_DATA_DIR, 'class_hour_distribution.csv')
CLASS_METHOD_PREFERENCE = os.path.join(PROCESSED_DATA_DIR, 'class_method_preference.csv')

# 初始化分析器（用于实时计算，作为备选）
behavior_analyzer = LearningBehaviorAnalyzer(DATA_DIR)
profile_analyzer = LearnerProfileAnalyzer(DATA_DIR)

# 缓存已加载的CSV数据
_csv_cache = {}

def load_csv_if_exists(file_path, cache_key=None):
    """加载CSV文件（带缓存）"""
    if cache_key and cache_key in _csv_cache:
        return _csv_cache[cache_key]

    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            if cache_key:
                _csv_cache[cache_key] = df
            return df
        except Exception as e:
            print(f"Warning: 无法加载CSV文件 {file_path}: {e}")
            return None
    return None

def get_major_name(major_code: str) -> str:
    """将专业编号转换为专业名称"""
    major_name_map = {
        'J78901': '计算机科学与技术',
        'J87654': '软件工程',
        'J23517': '数据科学与大数据技术',
        'J40192': '人工智能',
        'J57489': '网络工程',
    }
    return major_name_map.get(major_code, f"专业{major_code}")


def get_knowledge_name(knowledge_code: str) -> str:
    """将知识点编码转换为知识点名称"""
    knowledge_name_map = {
        'r8S3g': '程序控制',
        'm3D1v': '数据结构',
        'b3C9s': '基础语法',
        'g7R2j': '函数与模块',
        'k4W1c': '面向对象',
        's8Y2f': '文件操作',
        't5V9e': '算法设计',
        'y9W5d': '异常处理',
    }
    return knowledge_name_map.get(knowledge_code, f"知识点{knowledge_code}")


def get_method_name(method_code: str) -> str:
    """将编程方法编码转换为方法名称"""
    # 从完整的方法ID中提取简化的编码（如 Method_5Q4KoXthUuYz3bvrTDFm -> 5Q4Ko）
    # 或者直接使用映射
    if not method_code or method_code == 'Method_other':
        return '其他'
    
    # 提取方法编码（去掉 Method_ 前缀，取前5个字符）
    if method_code.startswith('Method_'):
        code = method_code[7:12]  # 取 Method_ 后面的5个字符
    else:
        code = method_code[:5] if len(method_code) >= 5 else method_code
    
    # 方法编码到名称的映射（根据实际数据调整）
    method_name_map = {
        '5Q4Ko': '方法1',
        'Cj9Ya': '方法2',
        'gj1NL': '方法3',
        'm8vwG': '方法4',
        'BXr9A': '方法5',
        'TDFm': '方法1',
        'ZL57': '方法2',
        'kQPd': '方法3',
        'YUoR': '方法4',
    }
    
    # 尝试匹配完整编码或简化编码
    if method_code in method_name_map:
        return method_name_map[method_code]
    elif code in method_name_map:
        return method_name_map[code]
    else:
        # 如果找不到映射，返回格式化的名称
        return f"方法{code}"

@app.route('/api/classes', methods=['GET'])
def get_classes():
    """获取所有专业列表（返回名称和编号）"""
    df = pd.read_csv(STUDENT_INFO_FILE)
    majors = sorted(df['major'].unique().tolist())
    
    # 返回包含名称和编号的对象列表，name用于前端显示
    classes = [
        {
            'code': major,
            'name': get_major_name(major)  # 前端直接显示这个name
        }
        for major in majors
    ]
    return jsonify(classes)

@app.route('/api/students', methods=['GET'])
def get_students():
    """获取所有学生列表（返回友好显示名称）"""
    df = pd.read_csv(STUDENT_INFO_FILE)
    
    students = []
    for idx, row in df.iterrows():
        student_id = row['student_ID']
        major_code = row['major']
        
        # 生成友好的显示名称（使用序号 + ID前6位）
        display_name = f"学生{idx+1:04d} ({student_id[:6]}...)"
        
        students.append({
            'student_ID': student_id,
            'major_code': major_code,
            'major_name': get_major_name(major_code),
            'display_name': display_name  # 前端显示这个
        })
    
    return jsonify(students)

@app.route('/api/students/<class_name>', methods=['GET'])
def get_students_by_class(class_name):
    """根据专业获取学生列表（返回友好显示名称）"""
    df = pd.read_csv(STUDENT_INFO_FILE)
    class_students = df[df['major'] == class_name].reset_index()
    
    students = []
    for idx, row in class_students.iterrows():
        student_id = row['student_ID']
        
        # 生成友好的显示名称（在该专业内的序号）
        display_name = f"学生{idx+1:04d} ({student_id[:6]}...)"
        
        students.append({
            'student_ID': student_id,
            'major_code': class_name,
            'major_name': get_major_name(class_name),
            'display_name': display_name  # 前端显示这个
        })
    
    return jsonify(students)


@app.route('/api/class-data/<class_name>', methods=['GET'])
def get_class_data(class_name):
    """获取班级数据（用于绿色和蓝色框）"""
    try:
        # 读取班级题目掌握情况
        df = pd.read_csv(CLASS_TITLE_MASTERY)
        class_data = df[df['class'] == f'Class{class_name[-1]}'].to_dict('records')
        
        # 可以添加更多数据处理逻辑
        return jsonify({
            'greenBox1': class_data[:10] if len(class_data) > 10 else class_data,  # 示例数据
            'greenBox2': class_data[10:20] if len(class_data) > 20 else class_data[10:],
            'blueBox1': {'summary': f'班级{class_name}的总体统计'},
            'blueBox2': {'summary': f'班级{class_name}的详细分析'}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/student-data/<student_id>', methods=['GET'])
def get_student_data(student_id):
    """获取学生数据（用于绿色和蓝色框）"""
    try:
        # 读取学生题目掌握情况
        df = pd.read_csv(INDIVIDUAL_TITLE_MASTERY)
        student_data = df[df['student_ID'] == student_id].to_dict('records')
        
        return jsonify({
            'greenBox1': student_data[:10] if len(student_data) > 10 else student_data,
            'greenBox2': student_data[10:20] if len(student_data) > 20 else student_data[10:],
            'blueBox1': {'summary': f'学生{student_id}的总体统计'},
            'blueBox2': {'summary': f'学生{student_id}的详细分析'}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== 4.2 个性化学习行为模式 API ====================

@app.route('/api/learning-profile/available-months', methods=['GET'])
def get_available_months():
    """获取可用月份列表"""
    try:
        student_id = request.args.get('student_id')
        class_name = request.args.get('class_name')

        # 优先从CSV读取
        if student_id:
            df = load_csv_if_exists(STUDENT_MONTHLY_STATS, 'student_monthly_stats')
            if df is not None:
                student_data = df[df['student_ID'] == student_id]
                if not student_data.empty:
                    months = sorted(student_data['month'].unique().tolist())
                    return jsonify({'months': months})
        elif class_name:
            # 从monthly_behavior_features读取
            df = load_csv_if_exists(MONTHLY_BEHAVIOR_FEATURES, 'monthly_behavior_features')
            if df is not None and 'month' in df.columns:
                months = sorted(df['month'].unique().tolist())
                return jsonify({'months': months})

        # 如果CSV不存在，使用实时计算
        months = behavior_analyzer.get_available_months(student_id, class_name)
        return jsonify({'months': months})
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'SERVER_ERROR'}), 500

@app.route('/api/learning-profile/behavior-features', methods=['GET'])
def get_behavior_features():
    """获取学习行为特征（蓝色框1 - Tab 1: 基础特征）"""
    try:
        student_id = request.args.get('student_id')
        class_name = request.args.get('class_name')
        month = request.args.get('month')

        # 优先从CSV读取（如果没有月份筛选）
        if not month and student_id:
            df = load_csv_if_exists(STUDENT_BEHAVIOR_FEATURES, 'student_behavior_features')
            if df is not None:
                student_data = df[df['student_ID'] == student_id]
                if not student_data.empty:
                    row = student_data.iloc[0]
                    # 计算对比数据（从CSV中计算平均值）- 确保字段顺序与文档一致
                    comparison = {
                        'submit_count_avg': float(df['submit_count'].mean()),
                        'active_days_avg': float(df['active_days'].mean()),
                        'question_count_avg': float(df['question_count'].mean()),
                        'correct_ratio_avg': float(df['correct_ratio_x'].mean())
                    }

                    # 确保pattern_ratio字段顺序与文档一致：submit_ratio, active_ratio, question_ratio, correct_ratio
                    pattern_ratio = {
                        'submit_ratio': float(row['submit_ratio']),
                        'active_ratio': float(row['active_ratio']),
                        'question_ratio': float(row['question_ratio']),
                        'correct_ratio': float(row['correct_ratio_y'])
                    }

                    result = {
                        'submit_count': int(row['submit_count']),
                        'active_days': int(row['active_days']),
                        'question_count': int(row['question_count']),
                        'correct_ratio': float(row['correct_ratio_x']),
                        'pattern': str(row['pattern']),
                        'pattern_ratio': pattern_ratio,
                        'comparison': comparison
                    }
                    return jsonify(result)

        # 如果有月份筛选或CSV不存在，使用实时计算
        features = behavior_analyzer.get_behavior_features(student_id, class_name, month)

        if student_id:
            pattern = behavior_analyzer.get_student_pattern(student_id, class_name, month)
        else:
            pattern = None

        # 获取pattern_ratio并确保字段顺序与文档一致：submit_ratio, active_ratio, question_ratio, correct_ratio
        pattern_ratio_raw = {}
        if student_id:
            pattern_ratio_raw = behavior_analyzer.get_pattern_ratio(student_id, class_name, month)

        pattern_ratio = {
            'submit_ratio': pattern_ratio_raw.get('submit_ratio', 0.0),
            'active_ratio': pattern_ratio_raw.get('active_ratio', 0.0),
            'question_ratio': pattern_ratio_raw.get('question_ratio', 0.0),
            'correct_ratio': pattern_ratio_raw.get('correct_ratio', 0.0)
        } if pattern_ratio_raw else {}

        # 获取comparison并确保字段顺序与文档一致：submit_count_avg, active_days_avg, question_count_avg, correct_ratio_avg
        comparison_raw = behavior_analyzer.get_comparison_data(student_id, class_name, month)
        comparison = {
            'submit_count_avg': comparison_raw.get('submit_count_avg', 0),
            'active_days_avg': comparison_raw.get('active_days_avg', 0),
            'question_count_avg': comparison_raw.get('question_count_avg', 0),
            'correct_ratio_avg': comparison_raw.get('correct_ratio_avg', 0.0)
        }

        # 确保字段顺序与文档一致：submit_count, active_days, question_count, correct_ratio, pattern, pattern_ratio, comparison
        result = {
            'submit_count': features.get('submit_count', 0),
            'active_days': features.get('active_days', 0),
            'question_count': features.get('question_count', 0),
            'correct_ratio': features.get('correct_ratio', 0.0),
            'pattern': pattern,
            'pattern_ratio': pattern_ratio,
            'comparison': comparison
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'SERVER_ERROR'}), 500

@app.route('/api/learning-profile/pattern-distribution', methods=['GET'])
def get_pattern_distribution():
    """获取学习模式分布（蓝色框1 - Tab 2: 学习模式）"""
    try:
        class_name = request.args.get('class_name')
        month = request.args.get('month')

        if not class_name:
            return jsonify({'error': 'class_name参数必填', 'code': 'INVALID_PARAMETER'}), 400

        # 优先从CSV读取（如果没有月份筛选）
        if not month:
            df = load_csv_if_exists(CLASS_PATTERN_DISTRIBUTION, 'class_pattern_distribution')
            if df is not None:
                class_data = df[df['class_name'] == class_name]
                if not class_data.empty:
                    patterns = {}
                    distribution = []
                    total = class_data.iloc[0]['total'] if 'total' in class_data.columns else 0

                    for _, row in class_data.iterrows():
                        pattern = str(row['pattern'])
                        count = int(row['count'])
                        percentage = float(row['percentage'])
                        patterns[pattern] = count
                        distribution.append({
                            'pattern': pattern,
                            'count': count,
                            'percentage': percentage
                        })

                    return jsonify({
                        'patterns': patterns,
                        'total': int(total),
                        'distribution': distribution
                    })

        # 如果有月份筛选或CSV不存在，使用实时计算
        distribution = behavior_analyzer.get_pattern_distribution(class_name, month)
        return jsonify(distribution)
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'SERVER_ERROR'}), 500

@app.route('/api/learning-profile/method-preference', methods=['GET'])
def get_method_preference():
    """获取编程方法偏好（蓝色框1 - Tab 3: 编程方法）"""
    try:
        student_id = request.args.get('student_id')
        class_name = request.args.get('class_name')
        month = request.args.get('month')
        top_n = int(request.args.get('top_n', 5))

        # 优先从CSV读取（如果没有月份筛选）
        if not month:
            if student_id:
                df = load_csv_if_exists(STUDENT_METHOD_PREFERENCE, 'student_method_preference')
                if df is not None:
                    student_data = df[df['student_ID'] == student_id].head(top_n)
                    if not student_data.empty:
                        method_distribution = []
                        for _, row in student_data.iterrows():
                            method_code = str(row['method'])
                            # 使用映射函数获取友好的方法名称
                            method_name = get_method_name(method_code) if method_code != 'Method_other' else '其他'
                            method_distribution.append({
                                'method': method_code,
                                'method_name': method_name,
                                'count': int(row['count']),
                                'ratio': float(row['ratio']),
                                'percentage': float(row['percentage'])
                            })
                        return jsonify({
                            'method_distribution': method_distribution,
                            'total_methods': len(method_distribution)
                        })
            elif class_name:
                df = load_csv_if_exists(CLASS_METHOD_PREFERENCE, 'class_method_preference')
                if df is not None:
                    class_data = df[df['class_name'] == class_name].head(top_n)
                    if not class_data.empty:
                        method_distribution = []
                        for _, row in class_data.iterrows():
                            method_code = str(row['method'])
                            # 使用映射函数获取友好的方法名称
                            method_name = get_method_name(method_code) if method_code != 'Method_other' else '其他'
                            method_distribution.append({
                                'method': method_code,
                                'method_name': method_name,
                                'count': int(row['count']),
                                'ratio': float(row['ratio']),
                                'percentage': float(row['percentage'])
                            })
                        return jsonify({
                            'method_distribution': method_distribution,
                            'total_methods': len(method_distribution)
                        })

        # 如果有月份筛选或CSV不存在，使用实时计算
        result = profile_analyzer.get_method_preference(student_id, class_name, month, top_n)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'SERVER_ERROR'}), 500

@app.route('/api/learning-profile/knowledge-mastery', methods=['GET'])
def get_knowledge_mastery():
    """获取知识点掌握情况（蓝色框1 - Tab 4: 知识点）"""
    try:
        student_id = request.args.get('student_id')
        class_name = request.args.get('class_name')
        month = request.args.get('month')

        # 优先从CSV读取（如果没有月份筛选且是学生查询）
        if not month and student_id:
            df = load_csv_if_exists(STUDENT_KNOWLEDGE_MASTERY, 'student_knowledge_mastery')
            if df is not None:
                student_data = df[df['student_ID'] == student_id]
                if not student_data.empty:
                    knowledge_stats = []
                    for _, row in student_data.iterrows():
                        knowledge_id = str(row['knowledge_id'])
                        # 使用映射函数获取知识点名称，如果CSV中有knowledge_name但格式不对，则使用映射
                        knowledge_name = get_knowledge_name(knowledge_id) if knowledge_id else str(row.get('knowledge_name', ''))
                        knowledge_stats.append({
                            'knowledge_id': knowledge_id,
                            'knowledge_name': knowledge_name,
                            'mastery': float(row['mastery']),
                            'mastery_percentage': float(row['mastery_percentage']),
                            'question_count': int(row['question_count']),
                            'submit_count': int(row['submit_count']),
                            'correct_count': int(row['correct_count']),
                            'level': str(row['level'])
                        })

                    # 统计汇总
                    good_count = len([k for k in knowledge_stats if k['level'] == 'good'])
                    medium_count = len([k for k in knowledge_stats if k['level'] == 'medium'])
                    poor_count = len([k for k in knowledge_stats if k['level'] == 'poor'])

                    # 确保summary字段顺序与文档一致：total_knowledge, good_count, medium_count, poor_count
                    return jsonify({
                        'knowledge_stats': knowledge_stats,
                        'summary': {
                            'total_knowledge': len(knowledge_stats),
                            'good_count': good_count,
                            'medium_count': medium_count,
                            'poor_count': poor_count
                        }
                    })

        # 如果有月份筛选或CSV不存在，使用实时计算
        result_raw = profile_analyzer.get_knowledge_mastery(student_id, class_name, month)

        # 确保字段顺序与文档一致
        knowledge_stats = []
        for item in result_raw.get('knowledge_stats', []):
            knowledge_stats.append({
                'knowledge_id': item.get('knowledge_id', ''),
                'knowledge_name': item.get('knowledge_name', ''),
                'mastery': item.get('mastery', 0.0),
                'mastery_percentage': item.get('mastery_percentage', 0.0),
                'question_count': item.get('question_count', 0),
                'submit_count': item.get('submit_count', 0),
                'correct_count': item.get('correct_count', 0),
                'level': item.get('level', '')
            })

        summary_raw = result_raw.get('summary', {})
        result = {
            'knowledge_stats': knowledge_stats,
            'summary': {
                'total_knowledge': summary_raw.get('total_knowledge', len(knowledge_stats)),
                'good_count': summary_raw.get('good_count', 0),
                'medium_count': summary_raw.get('medium_count', 0),
                'poor_count': summary_raw.get('poor_count', 0)
            }
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'SERVER_ERROR'}), 500

@app.route('/api/learning-profile/hour-distribution', methods=['GET'])
def get_hour_distribution():
    """获取24小时答题高峰时段（蓝色框2 - 上半部分）"""
    try:
        student_id = request.args.get('student_id')
        class_name = request.args.get('class_name')
        month = request.args.get('month')

        # 优先从CSV读取（如果没有月份筛选）
        if not month:
            if student_id:
                df = load_csv_if_exists(STUDENT_HOUR_DISTRIBUTION, 'student_hour_distribution')
                if df is not None:
                    student_data = df[df['student_ID'] == student_id]
                    if not student_data.empty:
                        hour_distribution = []
                        total_count = 0
                        for _, row in student_data.iterrows():
                            count = int(row['count'])
                            total_count += count
                            hour_distribution.append({
                                'hour': int(row['hour']),
                                'count': count,
                                'percentage': float(row['percentage'])
                            })

                        # 计算高峰时段（前5个）
                        sorted_hours = sorted(hour_distribution, key=lambda x: x['count'], reverse=True)
                        peak_hours = [h['hour'] for h in sorted_hours[:5]]

                        return jsonify({
                            'hour_distribution': hour_distribution,
                            'peak_hours': peak_hours,
                            'total_count': total_count
                        })
            elif class_name:
                df = load_csv_if_exists(CLASS_HOUR_DISTRIBUTION, 'class_hour_distribution')
                if df is not None:
                    class_data = df[df['class_name'] == class_name]
                    if not class_data.empty:
                        hour_distribution = []
                        total_count = 0
                        for _, row in class_data.iterrows():
                            count = int(row['count'])
                            total_count += count
                            hour_distribution.append({
                                'hour': int(row['hour']),
                                'count': count,
                                'percentage': float(row['percentage'])
                            })

                        sorted_hours = sorted(hour_distribution, key=lambda x: x['count'], reverse=True)
                        peak_hours = [h['hour'] for h in sorted_hours[:5]]

                        return jsonify({
                            'hour_distribution': hour_distribution,
                            'peak_hours': peak_hours,
                            'total_count': total_count
                        })

        # 如果有月份筛选或CSV不存在，使用实时计算
        result = profile_analyzer.get_hour_distribution(student_id, class_name, month)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'SERVER_ERROR'}), 500

@app.route('/api/learning-profile/monthly-heatmap', methods=['GET'])
def get_monthly_heatmap():
    """获取月度活动热力图数据（蓝色框2 - 下半部分）"""
    try:
        student_id = request.args.get('student_id')
        class_name = request.args.get('class_name')
        start_month = request.args.get('start_month')
        end_month = request.args.get('end_month')

        result = profile_analyzer.get_monthly_heatmap(student_id, class_name, start_month, end_month)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'SERVER_ERROR'}), 500

@app.route('/api/learning-profile/comprehensive-bluebox1', methods=['GET'])
def get_comprehensive_bluebox1():
    """获取综合数据（蓝色框1 - 所有Tab数据一次性获取）"""
    try:
        student_id = request.args.get('student_id')
        class_name = request.args.get('class_name')
        month = request.args.get('month')
        
        print(f"DEBUG comprehensive-bluebox1: student_id={student_id}, class_name={class_name}, month={month}")

        # Tab 1: 基础特征 - 直接复用get_behavior_features的逻辑，确保参数正确传递
        tab1_basic_features = {
            'submit_count': 0,
            'active_days': 0,
            'question_count': 0,
            'correct_ratio': 0.0,
            'pattern': None,
            'comparison': {}
        }
        
        tab1_loaded_from_csv = False
        
        # 优先从CSV读取（如果没有月份筛选）
        if not month and student_id:
            df = load_csv_if_exists(STUDENT_BEHAVIOR_FEATURES, 'student_behavior_features')
            if df is not None:
                student_data = df[df['student_ID'] == student_id]
                if not student_data.empty:
                    row = student_data.iloc[0]
                    # 计算对比数据（从CSV中计算平均值）
                    comparison = {
                        'submit_count_avg': float(df['submit_count'].mean()),
                        'active_days_avg': float(df['active_days'].mean()),
                        'question_count_avg': float(df['question_count'].mean()),
                        'correct_ratio_avg': float(df['correct_ratio_x'].mean())
                    }
                    
                    tab1_basic_features = {
                        'submit_count': int(row['submit_count']),
                        'active_days': int(row['active_days']),
                        'question_count': int(row['question_count']),
                        'correct_ratio': float(row['correct_ratio_x']),
                        'pattern': str(row['pattern']),
                        'comparison': comparison
                    }
                    tab1_loaded_from_csv = True
        
        # 如果有月份筛选或CSV不存在，使用实时计算
        if not tab1_loaded_from_csv:
            features = behavior_analyzer.get_behavior_features(student_id, class_name, month)
            
            if student_id:
                pattern = behavior_analyzer.get_student_pattern(student_id, class_name, month)
            else:
                pattern = None
            
            # 获取comparison数据
            comparison_raw = behavior_analyzer.get_comparison_data(student_id, class_name, month)
            comparison = {
                'submit_count_avg': comparison_raw.get('submit_count_avg', 0),
                'active_days_avg': comparison_raw.get('active_days_avg', 0),
                'question_count_avg': comparison_raw.get('question_count_avg', 0),
                'correct_ratio_avg': comparison_raw.get('correct_ratio_avg', 0.0)
            }
            
            tab1_basic_features = {
                'submit_count': features.get('submit_count', 0),
                'active_days': features.get('active_days', 0),
                'question_count': features.get('question_count', 0),
                'correct_ratio': features.get('correct_ratio', 0.0),
                'pattern': pattern,
                'comparison': comparison
            }

        # Tab 2: 学习模式 - 如果选择学生，显示该学生的学习模式；如果选择班级，显示班级分布（散点图）
        tab2_scatter_data = []
        
        if student_id:
            # 选择学生：显示该学生的学习模式（单个模式）- 柱状图数据
            student_pattern = tab1_basic_features.get('pattern')
            print(f"DEBUG: student_id={student_id}, student_pattern={student_pattern}")
            # 即使pattern为None，也返回柱状图数据（显示为"未知"或默认模式）
            all_patterns = ['探索尝试型', '广泛多样型', '集中针对型']
            for pattern in all_patterns:
                tab2_scatter_data.append({
                    'pattern': pattern,
                    'count': 1 if pattern == student_pattern else 0,
                    'is_current_student': pattern == student_pattern
                })
            print(f"DEBUG: tab2_scatter_data (student mode): {len(tab2_scatter_data)} items")
        else:
            # 选择班级：显示班级的学习模式分布（散点图数据）
            target_class_name = class_name
            if target_class_name:
                # 获取所有学生的特征数据用于散点图
                features_df = behavior_analyzer.get_all_students_features(target_class_name, month)
                if not features_df.empty:
                    # 分类学习模式
                    features_df = behavior_analyzer.classify_learning_pattern(features_df)
                    # 转换为散点图数据格式
                    for _, row in features_df.iterrows():
                        tab2_scatter_data.append({
                            'student_id': str(row['student_ID']),
                            'question_count': int(row['question_count']),
                            'correct_ratio': float(row['correct_ratio']),
                            'submit_count': int(row['submit_count']),
                            'active_days': int(row['active_days']),
                            'pattern': str(row['pattern'])
                        })
                print(f"DEBUG: tab2_scatter_data (class mode): {len(tab2_scatter_data)} items")

        # Tab 3: 编程方法偏好 - 确保数组项字段顺序：method, method_name, count, ratio, percentage
        tab3_response = get_method_preference()
        tab3_raw = tab3_response.get_json() if tab3_response.status_code == 200 else {}
        tab3_method_preference = {}
        if 'method_distribution' in tab3_raw:
            method_distribution = []
            for item in tab3_raw['method_distribution']:
                method_code = item.get('method', '')
                # 使用映射函数获取友好的方法名称
                method_name = get_method_name(method_code) if method_code != 'Method_other' else '其他'
                method_distribution.append({
                    'method': method_code,
                    'method_name': method_name,
                    'count': item.get('count', 0),
                    'ratio': item.get('ratio', 0.0),
                    'percentage': item.get('percentage', 0.0)
                })
            tab3_method_preference = {
                'method_distribution': method_distribution,
                'total_methods': tab3_raw.get('total_methods', len(method_distribution))
            }

        # Tab 4: 知识点掌握情况 - 确保数组项和summary字段顺序
        tab4_response = get_knowledge_mastery()
        tab4_raw = tab4_response.get_json() if tab4_response.status_code == 200 else {}
        tab4_knowledge_mastery = {}
        if 'knowledge_stats' in tab4_raw:
            knowledge_stats = []
            for item in tab4_raw['knowledge_stats']:
                knowledge_stats.append({
                    'knowledge_id': item.get('knowledge_id', ''),
                    'knowledge_name': item.get('knowledge_name', ''),
                    'mastery': item.get('mastery', 0.0),
                    'mastery_percentage': item.get('mastery_percentage', 0.0),
                    'question_count': item.get('question_count', 0),
                    'submit_count': item.get('submit_count', 0),
                    'correct_count': item.get('correct_count', 0),
                    'level': item.get('level', '')
                })
            summary_raw = tab4_raw.get('summary', {})
            tab4_knowledge_mastery = {
                'knowledge_stats': knowledge_stats,
                'summary': {
                    'total_knowledge': summary_raw.get('total_knowledge', len(knowledge_stats)),
                    'good_count': summary_raw.get('good_count', 0),
                    'medium_count': summary_raw.get('medium_count', 0),
                    'poor_count': summary_raw.get('poor_count', 0)
                }
            }

        return jsonify({
            'tab1_basic_features': tab1_basic_features,
            'tab2_scatter_data': tab2_scatter_data,
            'tab3_method_preference': tab3_method_preference,
            'tab4_knowledge_mastery': tab4_knowledge_mastery
        })
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'SERVER_ERROR'}), 500

@app.route('/api/learning-profile/comprehensive-bluebox2', methods=['GET'])
def get_comprehensive_bluebox2():
    """获取蓝色框2综合数据（24小时分布 + 月度热力图）"""
    try:
        student_id = request.args.get('student_id')
        class_name = request.args.get('class_name')
        month = request.args.get('month')
        start_month = request.args.get('start_month')
        end_month = request.args.get('end_month')

        # 24小时答题高峰时段（已优化为优先从CSV读取）
        hour_result = get_hour_distribution()
        hour_distribution_raw = hour_result.get_json() if hour_result.status_code == 200 else {}

        # 根据文档，hour_distribution数组项只包含hour和count，不包含percentage
        # 确保字段顺序：hour, count
        hour_distribution = {}
        if 'hour_distribution' in hour_distribution_raw:
            hour_list = []
            for item in hour_distribution_raw['hour_distribution']:
                # 确保字段顺序与文档一致：hour, count
                hour_list.append({
                    'hour': item.get('hour', 0),
                    'count': item.get('count', 0)
                })
            hour_distribution = {
                'hour_distribution': hour_list,
                'peak_hours': hour_distribution_raw.get('peak_hours', [])
            }

        # 月度活动热力图 - 根据文档，comprehensive-bluebox2中不包含summary字段
        # 确保字段顺序：day, count, level
        monthly_heatmap_raw = profile_analyzer.get_monthly_heatmap(student_id, class_name, start_month, end_month)
        monthly_heatmap = {}
        if 'heatmap_data' in monthly_heatmap_raw:
            heatmap_data = []
            for month_data in monthly_heatmap_raw['heatmap_data']:
                days = []
                for day_item in month_data.get('days', []):
                    # 确保字段顺序与文档一致：day, count, level
                    days.append({
                        'day': day_item.get('day', 0),
                        'count': day_item.get('count', 0),
                        'level': day_item.get('level', 'none')
                    })
                # 确保字段顺序：month, month_name, days
                heatmap_data.append({
                    'month': month_data.get('month', ''),
                    'month_name': month_data.get('month_name', ''),
                    'days': days
                })
            monthly_heatmap = {
                'heatmap_data': heatmap_data
            }

        # 月度学习趋势
        monthly_stats = profile_analyzer.get_monthly_stats(student_id, class_name)

        return jsonify({
            'hour_distribution': hour_distribution,
            'monthly_heatmap': monthly_heatmap,
            'monthly_stats': monthly_stats
        })
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'SERVER_ERROR'}), 500


@app.route('/hybridaction/zybTrackerStatisticsAction', methods=['GET'])
def hybrid_tracker_statistics():
    """
    兼容旧版可视化前端使用的 JSONP 接口。
    支持 query 参数:
        data: json 字符串，可包含 class / student_ID 等过滤条件
        __callback__: JSONP 回调名称
    """
    payload = safe_json_loads(request.args.get('data', '{}'))
    callback = request.args.get('__callback__') or request.args.get('callback')

    selected_class = payload.get('class') or payload.get('className')
    student_id = payload.get('student_ID') or payload.get('studentId')

    class_summary, class_details, available_classes = build_class_summary(selected_class)
    student_details, available_students = build_student_mastery(student_id)
    knowledge_snapshot = build_knowledge_snapshot(selected_class, student_id)

    tracker_payload = {
        'code': 0,
        'message': 'success',
        'requested': {
            'class': selected_class,
            'student': student_id,
        },
        'available': {
            'classes': available_classes,
            'students': available_students,
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'data': {
            'classSummary': class_summary,
            'classDetails': class_details,
            'studentDetails': student_details,
            'knowledge': knowledge_snapshot,
        }
    }

    if callback:
        body = f"{callback}({json.dumps(tracker_payload, ensure_ascii=False)})"
        return Response(body, mimetype='application/javascript')

    return jsonify(tracker_payload)

if __name__ == '__main__':
    app.run(debug=True, port=5000)