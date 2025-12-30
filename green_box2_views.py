from flask import Blueprint, jsonify, request
import pandas as pd
import numpy as np
import os
from functools import lru_cache
from typing import Dict, Any, List, Optional

green_box2_bp = Blueprint('green_box2', __name__, url_prefix='/api/green/box2')

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
MASTER_DIR = os.path.join(DATA_DIR, 'mastery')
SUBMIT_DIR = os.path.join(DATA_DIR, 'Data_SubmitRecord')
LEARNING_BEHAVIOR_DIR = os.path.join(DATA_DIR, 'learning_behavior')
STUDENT_INFO_FILE = os.path.join(DATA_DIR, 'Data_StudentInfo.csv')

INDIVIDUAL_KNOWLEDGE_MASTERY = os.path.join(MASTER_DIR, 'individual_knowledge_mastery.csv')
STUDENT_KNOWLEDGE_MASTERY = os.path.join(LEARNING_BEHAVIOR_DIR, 'student_knowledge_mastery.csv')


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.astype(str).str.replace('\ufeff', '', regex=False).str.strip()
    return df


def _normalize_column_name(df: pd.DataFrame, target: str) -> pd.DataFrame:
    if target in df.columns:
        return df
    matches = [col for col in df.columns if col.lower() == target.lower()]
    if matches:
        df = df.rename(columns={matches[0]: target})
    return df


@lru_cache(maxsize=1)
def load_individual_knowledge_mastery() -> pd.DataFrame:
    """加载个人知识点掌握度数据"""
    if os.path.exists(INDIVIDUAL_KNOWLEDGE_MASTERY):
        df = pd.read_csv(INDIVIDUAL_KNOWLEDGE_MASTERY)
        df = _normalize_columns(df)
        return df
    return pd.DataFrame()


@lru_cache(maxsize=1)
def load_student_knowledge_mastery() -> pd.DataFrame:
    """加载学生知识点掌握度数据（备选）"""
    if os.path.exists(STUDENT_KNOWLEDGE_MASTERY):
        df = pd.read_csv(STUDENT_KNOWLEDGE_MASTERY)
        df = _normalize_columns(df)
        return df
    return pd.DataFrame()


def get_class_name_from_major(major_name: str) -> Optional[str]:
    """通过major名称获取对应的class名称"""
    if not major_name:
        return None
    
    # 如果已经是Class格式，直接返回
    if major_name.startswith('Class'):
        return major_name
    
    # 通过学生信息查找对应的class
    try:
        student_info = pd.read_csv(STUDENT_INFO_FILE)
        student_info = _normalize_columns(student_info)
        
        # 找到该major的学生
        major_students = student_info[student_info['major'] == major_name]
        if major_students.empty:
            return None
        
        # 获取这些学生的ID
        student_ids = set(major_students['student_ID'].dropna().astype(str).tolist())
        
        # 在所有提交记录中查找这些学生属于哪个class
        csv_files = [f for f in os.listdir(SUBMIT_DIR) if f.startswith('SubmitRecord-Class') and f.endswith('.csv')]
        for filename in csv_files:
            filepath = os.path.join(SUBMIT_DIR, filename)
            df = pd.read_csv(filepath)
            df = _normalize_columns(df)
            if 'student_ID' in df.columns and 'class' in df.columns:
                # 检查是否有该major的学生
                if any(sid in df['student_ID'].values for sid in student_ids):
                    # 返回该文件的class名称
                    class_name = df['class'].iloc[0] if not df.empty else None
                    if class_name:
                        return class_name
    except Exception as e:
        print(f"Warning: 无法查找class名称: {e}")
    
    return None


def load_submit_records(class_name: Optional[str] = None, month: Optional[str] = None) -> pd.DataFrame:
    """加载提交记录"""
    # 如果class_name是major格式（如J78901），先转换为class格式（如Class1）
    actual_class_name = get_class_name_from_major(class_name) if class_name else None
    
    if actual_class_name:
        filename = f'SubmitRecord-{actual_class_name}.csv'
        filepath = os.path.join(SUBMIT_DIR, filename)
        if not os.path.exists(filepath):
            return pd.DataFrame()
        df = pd.read_csv(filepath)
    elif class_name and class_name.startswith('Class'):
        # 直接使用class名称
        filename = f'SubmitRecord-{class_name}.csv'
        filepath = os.path.join(SUBMIT_DIR, filename)
        if not os.path.exists(filepath):
            return pd.DataFrame()
        df = pd.read_csv(filepath)
    else:
        # 加载所有班级的数据
        csv_files = [f for f in os.listdir(SUBMIT_DIR) if f.startswith('SubmitRecord-Class') and f.endswith('.csv')]
        if not csv_files:
            return pd.DataFrame()
        dfs = []
        for filename in csv_files:
            filepath = os.path.join(SUBMIT_DIR, filename)
            df = pd.read_csv(filepath)
            dfs.append(df)
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    
    if df.empty:
        return df
    
    df = _normalize_columns(df)
    
    # 如果class_name是major格式，需要进一步筛选该major的学生
    if class_name and not class_name.startswith('Class') and actual_class_name:
        # 通过学生信息找到该major的所有学生ID
        try:
            student_info = pd.read_csv(STUDENT_INFO_FILE)
            student_info = _normalize_columns(student_info)
            major_students = student_info[student_info['major'] == class_name]
            if not major_students.empty:
                student_ids = set(major_students['student_ID'].dropna().astype(str).tolist())
                df = df[df['student_ID'].isin(student_ids)]
        except Exception as e:
            print(f"Warning: 无法筛选major学生: {e}")
    
    # 添加时间字段
    if 'time' in df.columns:
        df['datetime'] = pd.to_datetime(df['time'], unit='s', errors='coerce')
        df['month'] = df['datetime'].dt.to_period('M').astype(str)
    
    # 月份筛选
    if month:
        df = df[df['month'] == month]
    
    # 筛选有效记录
    valid_states = ['Absolutely_Correct', 'Partially_Correct', 'Error1', 'Error2']
    if 'state' in df.columns:
        df = df[df['state'].isin(valid_states)]
    
    return df


def get_student_ids(class_name: Optional[str] = None, student_id: Optional[str] = None) -> List[str]:
    """获取学生ID列表"""
    if student_id:
        return [student_id]
    
    if class_name:
        # 如果class_name是major格式（如J78901），通过学生信息文件获取该major的所有学生
        if not class_name.startswith('Class'):
            try:
                student_info = pd.read_csv(STUDENT_INFO_FILE)
                student_info = _normalize_columns(student_info)
                major_students = student_info[student_info['major'] == class_name]
                if not major_students.empty:
                    student_ids = major_students['student_ID'].dropna().unique().tolist()
                    print(f"GreenBox2: 从学生信息获取到 {len(student_ids)} 个学生ID (major: {class_name})")
                    return student_ids
            except Exception as e:
                print(f"Warning: 无法从学生信息获取学生ID: {e}")
        
        # 如果class_name是Class格式，或者上面的方法失败，从提交记录获取
        df = load_submit_records(class_name)
        if not df.empty and 'student_ID' in df.columns:
            student_ids = df['student_ID'].dropna().unique().tolist()
            if student_ids:
                print(f"GreenBox2: 从提交记录获取到 {len(student_ids)} 个学生ID (class: {class_name})")
                return student_ids
    
    # 获取所有学生
    df = load_submit_records()
    if df.empty or 'student_ID' not in df.columns:
        return []
    student_ids = df['student_ID'].dropna().unique().tolist()
    print(f"GreenBox2: 获取到 {len(student_ids)} 个所有学生ID")
    return student_ids


def calculate_learning_duration(submit_df: pd.DataFrame) -> float:
    """计算学习时长（小时）"""
    if submit_df.empty:
        return 0.0
    
    # 方案1：基于timeconsume累加（秒转小时）
    if 'timeconsume' in submit_df.columns:
        timeconsume = pd.to_numeric(submit_df['timeconsume'], errors='coerce')
        total_seconds = timeconsume.sum()
        if pd.notna(total_seconds) and total_seconds > 0:
            return round(total_seconds / 3600, 2)
    
    # 方案2：基于时间跨度（备选）
    if 'time' in submit_df.columns:
        time_values = pd.to_numeric(submit_df['time'], errors='coerce').dropna()
        if len(time_values) > 0:
            time_span = time_values.max() - time_values.min()
            return round(time_span / 3600 / 24, 2)  # 天数转小时
    
    return 0.0


def calculate_coding_habits(submit_df: pd.DataFrame) -> float:
    """计算编程习惯得分（0-1）"""
    if submit_df.empty or 'method' not in submit_df.columns or 'title_ID' not in submit_df.columns:
        return 0.0
    
    # 方法使用的一致性（同一题目使用相同方法的比例）
    title_method_groups = submit_df.groupby('title_ID')['method'].apply(lambda x: x.nunique())
    consistency = (title_method_groups == 1).sum() / len(title_method_groups) if len(title_method_groups) > 0 else 0.0
    
    # 方法使用的多样性（使用不同方法的数量 / 总题目数）
    unique_methods = submit_df['method'].nunique()
    unique_titles = submit_df['title_ID'].nunique()
    diversity = min(unique_methods / unique_titles, 1.0) if unique_titles > 0 else 0.0
    
    # 方法选择的合理性（正确率与方法的关联度）
    if 'state' in submit_df.columns:
        correct_states = ['Absolutely_Correct', 'Partially_Correct']
        submit_df['is_correct'] = submit_df['state'].isin(correct_states)
        method_correct_rate = submit_df.groupby('method')['is_correct'].mean()
        effectiveness = method_correct_rate.mean() if len(method_correct_rate) > 0 else 0.0
    else:
        effectiveness = 0.0
    
    # 综合得分
    coding_habits_score = (
        consistency * 0.4 +
        diversity * 0.3 +
        effectiveness * 0.3
    )
    
    return round(max(0.0, min(1.0, coding_habits_score)), 4)


def calculate_average_score(submit_df: pd.DataFrame) -> float:
    """计算平均得分（0-4）"""
    if submit_df.empty or 'score' not in submit_df.columns:
        return 0.0
    
    scores = pd.to_numeric(submit_df['score'], errors='coerce').dropna()
    if len(scores) > 0:
        return round(scores.mean(), 2)
    return 0.0


def calculate_submit_count(submit_df: pd.DataFrame) -> int:
    """计算提交次数"""
    return len(submit_df)


def calculate_knowledge_mastery(student_id: str) -> float:
    """计算知识掌握程度（0-80%）"""
    # 优先使用 individual_knowledge_mastery
    mastery_df = load_individual_knowledge_mastery()
    if not mastery_df.empty and 'student_ID' in mastery_df.columns:
        student_mastery = mastery_df[mastery_df['student_ID'] == student_id]
        if not student_mastery.empty:
            if 'knowledge_mastery_score' in student_mastery.columns:
                avg_mastery = student_mastery['knowledge_mastery_score'].mean()
                mastery_percentage = min(avg_mastery * 100, 80)
                return round(mastery_percentage, 2)
    
    # 备选：使用 student_knowledge_mastery
    student_mastery_df = load_student_knowledge_mastery()
    if not student_mastery_df.empty and 'student_ID' in student_mastery_df.columns:
        student_mastery = student_mastery_df[student_mastery_df['student_ID'] == student_id]
        if not student_mastery.empty:
            if 'mastery_percentage' in student_mastery.columns:
                avg_mastery = student_mastery['mastery_percentage'].mean()
                return round(min(avg_mastery, 80), 2)
            elif 'mastery' in student_mastery.columns:
                avg_mastery = student_mastery['mastery'].mean()
                mastery_percentage = min(avg_mastery * 100, 80)
                return round(mastery_percentage, 2)
    
    # 如果都没有，返回一个默认值（比如平均值），确保至少显示一些数据
    # 这里返回0，让前端至少能看到数据点
    return 0.0


def calculate_correlation(x_values: List[float], y_values: List[float]) -> float:
    """计算相关系数（使用numpy）"""
    if len(x_values) < 2 or len(y_values) < 2 or len(x_values) != len(y_values):
        return 0.0
    
    try:
        x_arr = np.array(x_values)
        y_arr = np.array(y_values)
        
        # 计算均值
        x_mean = np.mean(x_arr)
        y_mean = np.mean(y_arr)
        
        # 计算标准差
        x_std = np.std(x_arr, ddof=0)
        y_std = np.std(y_arr, ddof=0)
        
        if x_std == 0 or y_std == 0:
            return 0.0
        
        # 计算相关系数
        correlation = np.mean((x_arr - x_mean) * (y_arr - y_mean)) / (x_std * y_std)
        
        return round(float(correlation), 4) if not np.isnan(correlation) else 0.0
    except:
        return 0.0


def build_scatter_plot_data(
    plot_key: str,
    title: str,
    x_axis_label: str,
    student_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """构建散点图数据"""
    if not student_data:
        return {
            'title': title,
            'x_axis_label': x_axis_label,
            'y_axis_label': '知识掌握程度(%)',
            'data': [],
            'statistics': {
                'x_min': 0,
                'x_max': 1,
                'y_min': 0,
                'y_max': 80,
                'correlation': 0.0,
                'data_count': 0
            }
        }
    
    # 提取数据
    data_points = []
    x_values = []
    y_values = []
    
    for item in student_data:
        x_value = item.get('x_value', 0)
        y_value = item.get('y_value', 0)
        data_points.append({
            'student_ID': item.get('student_ID', ''),
            'x_value': x_value,
            'y_value': y_value,
            'student_name': item.get('student_name')
        })
        x_values.append(x_value)
        y_values.append(y_value)
    
    # 计算统计信息
    x_min = min(x_values) if x_values else 0
    x_max = max(x_values) if x_values else 1
    y_min = 0
    y_max = 80
    correlation = calculate_correlation(x_values, y_values)
    
    return {
        'title': title,
        'x_axis_label': x_axis_label,
        'y_axis_label': '知识掌握程度(%)',
        'data': data_points,
        'statistics': {
            'x_min': round(x_min, 2),
            'x_max': round(x_max, 2),
            'y_min': y_min,
            'y_max': y_max,
            'correlation': correlation,
            'data_count': len(data_points)
        }
    }


def build_learning_mode_analysis_payload(
    class_name: Optional[str] = None,
    student_id: Optional[str] = None,
    month: Optional[str] = None
) -> Dict[str, Any]:
    """构建学习模式分析数据"""
    student_ids = get_student_ids(class_name, student_id)
    
    if not student_ids:
        return {
            'class': class_name,
            'student': student_id,
            'month': month,
            'scatter_plots': {
                'learning_duration': build_scatter_plot_data('learning_duration', '知识掌握程度 vs 学习时长', '学习时长', []),
                'coding_habits': build_scatter_plot_data('coding_habits', '知识掌握程度 vs 编程习惯', '编程习惯', []),
                'average_score': build_scatter_plot_data('average_score', '知识掌握程度 vs 平均得分', '平均得分', []),
                'submit_count': build_scatter_plot_data('submit_count', '知识掌握程度 vs 提交次数', '提交次数', [])
            }
        }
    
    # 加载提交记录
    submit_df = load_submit_records(class_name, month)
    
    # 为每个学生计算指标
    student_data_learning_duration = []
    student_data_coding_habits = []
    student_data_average_score = []
    student_data_submit_count = []
    
    print(f"GreenBox2: 开始处理 {len(student_ids)} 个学生")
    processed_count = 0
    
    for sid in student_ids:
        student_submit_df = submit_df[submit_df['student_ID'] == sid] if not submit_df.empty else pd.DataFrame()
        
        # 计算知识掌握程度
        mastery = calculate_knowledge_mastery(sid)
        
        # 无论是否有提交记录，只要有掌握度数据就添加数据点
        if mastery > 0 or not student_submit_df.empty:
            if not student_submit_df.empty:
                processed_count += 1
                # 学习时长
                learning_duration = calculate_learning_duration(student_submit_df)
                student_data_learning_duration.append({
                    'student_ID': sid,
                    'x_value': learning_duration,
                    'y_value': mastery
                })
                
                # 编程习惯
                coding_habits = calculate_coding_habits(student_submit_df)
                student_data_coding_habits.append({
                    'student_ID': sid,
                    'x_value': coding_habits,
                    'y_value': mastery
                })
                
                # 平均得分
                avg_score = calculate_average_score(student_submit_df)
                student_data_average_score.append({
                    'student_ID': sid,
                    'x_value': avg_score,
                    'y_value': mastery
                })
                
                # 提交次数
                submit_count = calculate_submit_count(student_submit_df)
                student_data_submit_count.append({
                    'student_ID': sid,
                    'x_value': submit_count,
                    'y_value': mastery
                })
            else:
                # 即使没有提交记录，如果有掌握度数据，也添加数据点（x值为0）
                student_data_learning_duration.append({
                    'student_ID': sid,
                    'x_value': 0.0,
                    'y_value': mastery
                })
                student_data_coding_habits.append({
                    'student_ID': sid,
                    'x_value': 0.0,
                    'y_value': mastery
                })
                student_data_average_score.append({
                    'student_ID': sid,
                    'x_value': 0.0,
                    'y_value': mastery
                })
                student_data_submit_count.append({
                    'student_ID': sid,
                    'x_value': 0,
                    'y_value': mastery
                })
    
    print(f"GreenBox2: 处理完成，有提交记录的学生: {processed_count}, 学习时长数据点: {len(student_data_learning_duration)}, 编程习惯数据点: {len(student_data_coding_habits)}, 平均得分数据点: {len(student_data_average_score)}, 提交次数数据点: {len(student_data_submit_count)}")
    
    return {
        'class': class_name,
        'student': student_id,
        'month': month,
        'scatter_plots': {
            'learning_duration': build_scatter_plot_data('learning_duration', '知识掌握程度 vs 学习时长', '学习时长', student_data_learning_duration),
            'coding_habits': build_scatter_plot_data('coding_habits', '知识掌握程度 vs 编程习惯', '编程习惯', student_data_coding_habits),
            'average_score': build_scatter_plot_data('average_score', '知识掌握程度 vs 平均得分', '平均得分', student_data_average_score),
            'submit_count': build_scatter_plot_data('submit_count', '知识掌握程度 vs 提交次数', '提交次数', student_data_submit_count)
        }
    }


@green_box2_bp.route('/learning-mode-analysis', methods=['GET'])
def get_learning_mode_analysis():
    """获取学习模式分析数据"""
    try:
        class_name = request.args.get('class')
        student_id = request.args.get('student_ID')
        month = request.args.get('month')
        
        payload = build_learning_mode_analysis_payload(class_name, student_id, month)
        return jsonify(payload)
    except ValueError as exc:
        return jsonify({'error': str(exc), 'code': 'INVALID_PARAMETER'}), 400
    except Exception as exc:
        return jsonify({'error': str(exc), 'code': 'SERVER_ERROR'}), 500

