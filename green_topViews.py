from flask import Blueprint, jsonify
import pandas as pd
import os
from functools import lru_cache
from typing import Dict, Any, List
import glob
import random

green_top_bp = Blueprint('green_top', __name__, url_prefix='/api/green/top')

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
MASTER_DIR = os.path.join(DATA_DIR, 'mastery')
SUBMIT_DIR = os.path.join(DATA_DIR, 'Data_SubmitRecord')

TITLE_INFO_FILE = os.path.join(DATA_DIR, 'Data_TitleInfo.csv')
STUDENT_INFO_FILE = os.path.join(DATA_DIR, 'Data_StudentInfo.csv')
INDIVIDUAL_TITLE_FILE = os.path.join(MASTER_DIR, 'individual_title_mastery.csv')
INDIVIDUAL_KNOWLEDGE_FILE = os.path.join(MASTER_DIR, 'individual_knowledge_mastery.csv')
MAJOR_KNOWLEDGE_FILE = os.path.join(MASTER_DIR, 'major_knowledge_mastery.csv')


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """标准化列名，去除BOM和空格"""
    df.columns = df.columns.astype(str).str.replace('\ufeff', '', regex=False).str.strip()
    return df


def _normalize_column_name(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """标准化特定列名（大小写不敏感）"""
    if target in df.columns:
        return df
    matches = [col for col in df.columns if col.lower() == target.lower()]
    if matches:
        df = df.rename(columns={matches[0]: target})
    return df


@lru_cache(maxsize=1)
def load_title_info() -> pd.DataFrame:
    """加载题目信息"""
    df = pd.read_csv(TITLE_INFO_FILE, encoding='utf-8-sig')
    df = _normalize_columns(df)
    for col in ['title_ID', 'knowledge', 'sub_knowledge', 'score']:
        df = _normalize_column_name(df, col)
    return df[['title_ID', 'knowledge', 'sub_knowledge', 'score']].drop_duplicates()


@lru_cache(maxsize=1)
def load_student_info() -> pd.DataFrame:
    """加载学生信息"""
    df = pd.read_csv(STUDENT_INFO_FILE, encoding='utf-8-sig')
    df = _normalize_columns(df)
    for col in ['student_ID', 'major']:
        df = _normalize_column_name(df, col)
    return df[['student_ID', 'major']].drop_duplicates()


@lru_cache(maxsize=1)
def load_submit_records() -> pd.DataFrame:
    """加载所有提交记录"""
    csv_files = glob.glob(os.path.join(SUBMIT_DIR, 'SubmitRecord-Class*.csv'))
    if not csv_files:
        return pd.DataFrame(columns=['student_ID', 'title_ID', 'class', 'state', 'score'])
    
    frames = []
    for path in csv_files:
        df = pd.read_csv(path, encoding='utf-8-sig')
        df = _normalize_columns(df)
        for col in ['student_ID', 'title_ID', 'class', 'state', 'score']:
            df = _normalize_column_name(df, col)
        if 'student_ID' in df.columns and 'title_ID' in df.columns:
            # 保留所有需要的列
            available_cols = ['student_ID', 'title_ID', 'class']
            if 'state' in df.columns:
                available_cols.append('state')
            if 'score' in df.columns:
                available_cols.append('score')
            frames.append(df[available_cols])
    
    if not frames:
        return pd.DataFrame(columns=['student_ID', 'title_ID', 'class', 'state', 'score'])
    
    return pd.concat(frames, ignore_index=True)


@lru_cache(maxsize=1)
def load_individual_knowledge_mastery() -> pd.DataFrame:
    """加载个人知识点掌握度"""
    df = pd.read_csv(INDIVIDUAL_KNOWLEDGE_FILE)
    df = _normalize_columns(df)
    for col in ['student_ID', 'knowledge', 'knowledge_mastery_score']:
        df = _normalize_column_name(df, col)
    return df


@lru_cache(maxsize=1)
def load_individual_title_mastery() -> pd.DataFrame:
    """加载个人题目掌握度"""
    df = pd.read_csv(INDIVIDUAL_TITLE_FILE)
    df = _normalize_columns(df)
    return df


@lru_cache(maxsize=1)
def load_major_knowledge_mastery() -> pd.DataFrame:
    """加载专业知识点掌握度"""
    df = pd.read_csv(MAJOR_KNOWLEDGE_FILE)
    df = _normalize_columns(df)
    for col in ['major', 'knowledge', 'knowledge_mastery_score']:
        df = _normalize_column_name(df, col)
    return df


def get_major_name(major_code: str) -> str:
    """将专业编号转换为专业名称"""
    # 专业编号到专业名称的映射
    # 如果没有映射文件，可以根据编号生成或使用默认名称
    major_name_map = {
        'J78901': '计算机科学与技术',
        'J87654': '软件工程',
        'J23517': '数据科学与大数据技术',
        'J40192': '人工智能',
        'J57489': '网络工程',
        # 可以根据实际数据添加更多映射
    }
    
    # 如果存在映射，返回映射名称；否则返回格式化的名称
    if major_code in major_name_map:
        return major_name_map[major_code]
    else:
        # 如果没有映射，返回格式化的名称
        return f"专业{major_code}"


def get_major_category(major_code: str) -> str:
    """获取专业类别（用于颜色映射）"""
    # 可以根据专业编号的前缀或其他规则分类
    # 这里简化处理，可以根据实际需求调整
    category_map = {
        'J78901': '计算机类',
        'J87654': '计算机类',
        'J23517': '数据类',
        'J40192': '人工智能类',
        'J57489': '网络类',
    }
    return category_map.get(major_code, '其他类')


def get_student_learning_pattern(student_id: str, submit_records: pd.DataFrame, 
                                  title_info: pd.DataFrame) -> str:
    """根据提交行为判断学生学习模式（简化版）"""
    student_submits = submit_records[submit_records['student_ID'] == student_id]
    if student_submits.empty:
        return "未知型"
    
    # 计算尝试题目数量和重复提交率
    unique_titles = student_submits['title_ID'].nunique()
    total_submits = len(student_submits)
    repeat_rate = total_submits / unique_titles if unique_titles > 0 else 0
    
    if repeat_rate > 3:
        return "反复练习型"
    elif unique_titles > 30:
        return "探索尝试型"
    else:
        return "稳步推进型"


def calculate_student_overall_mastery(student_id: str, 
                                       individual_knowledge: pd.DataFrame) -> float:
    """计算学生个人综合掌握度"""
    student_knowledge = individual_knowledge[individual_knowledge['student_ID'] == student_id]
    if student_knowledge.empty:
        return 0.0
    return float(student_knowledge['knowledge_mastery_score'].mean() * 100)


def calculate_student_accuracy(student_id: str, submit_records: pd.DataFrame) -> Dict[str, Any]:
    """计算学生正确率和总提交次数"""
    student_submits = submit_records[submit_records['student_ID'] == student_id]
    if student_submits.empty:
        return {'accuracy': 0.0, 'total_submits': 0}
    
    total = len(student_submits)
    # 假设state字段存在，Absolutely_Correct为正确
    if 'state' in student_submits.columns:
        correct = len(student_submits[student_submits['state'] == 'Absolutely_Correct'])
        accuracy = (correct / total * 100) if total > 0 else 0.0
    else:
        accuracy = 0.0
    
    return {'accuracy': accuracy, 'total_submits': total}


def batch_calculate_student_stats(student_ids: List[str], 
                                   individual_knowledge: pd.DataFrame,
                                   submit_records: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """批量计算学生统计信息（优化性能）"""
    stats = {}
    
    # 批量计算掌握度
    mastery_data = individual_knowledge[individual_knowledge['student_ID'].isin(student_ids)]
    mastery_by_student = mastery_data.groupby('student_ID')['knowledge_mastery_score'].mean() * 100
    
    # 批量计算准确率和提交次数
    submit_data = submit_records[submit_records['student_ID'].isin(student_ids)]
    
    if 'state' in submit_data.columns:
        accuracy_data = submit_data.groupby('student_ID').agg({
            'title_ID': 'count',  # 总提交次数
            'state': lambda x: (x == 'Absolutely_Correct').sum()  # 正确次数
        })
        accuracy_data.columns = ['total_submits', 'correct_submits']
        accuracy_data['accuracy'] = (accuracy_data['correct_submits'] / accuracy_data['total_submits'] * 100).fillna(0)
    else:
        accuracy_data = submit_data.groupby('student_ID').size().to_frame('total_submits')
        accuracy_data['accuracy'] = 0.0
    
    # 组合结果
    for student_id in student_ids:
        stats[student_id] = {
            'overall_mastery': float(mastery_by_student.get(student_id, 0.0)),
            'accuracy': float(accuracy_data.loc[student_id, 'accuracy']) if student_id in accuracy_data.index else 0.0,
            'total_submits': int(accuracy_data.loc[student_id, 'total_submits']) if student_id in accuracy_data.index else 0
        }
    
    return stats


def stratified_sample_students(major: str, student_info: pd.DataFrame, 
                                submit_records: pd.DataFrame, 
                                title_info: pd.DataFrame,
                                sample_size: int = 15) -> List[str]:
    """按专业+学习模式分层抽样代表性学生"""
    major_students = student_info[student_info['major'] == major]['student_ID'].tolist()
    
    if len(major_students) <= sample_size:
        return major_students
    
    # 按学习模式分组
    pattern_groups = {}
    for student_id in major_students:
        pattern = get_student_learning_pattern(student_id, submit_records, title_info)
        if pattern not in pattern_groups:
            pattern_groups[pattern] = []
        pattern_groups[pattern].append(student_id)
    
    # 按比例抽样
    sampled = []
    remaining = sample_size
    total_students = len(major_students)
    
    for pattern, students in pattern_groups.items():
        if remaining <= 0:
            break
        proportion = len(students) / total_students
        n = max(1, int(proportion * sample_size))
        n = min(n, len(students), remaining)
        sampled.extend(random.sample(students, n))
        remaining -= n
    
    # 如果还没满，随机补充
    if len(sampled) < sample_size:
        remaining_students = [s for s in major_students if s not in sampled]
        if remaining_students:
            need = sample_size - len(sampled)
            sampled.extend(random.sample(remaining_students, min(need, len(remaining_students))))
    
    return sampled[:sample_size]


def get_unique_pattern_students(major: str, student_info: pd.DataFrame, 
                                 submit_records: pd.DataFrame, 
                                 title_info: pd.DataFrame,
                                 student_patterns: Dict[str, str]) -> List[str]:
    """获取每个专业-学习模式组合的唯一代表性学生"""
    major_students = student_info[student_info['major'] == major]['student_ID'].tolist()
    
    if not major_students:
        return []
    
    # 按学习模式分组（使用预计算的模式）
    pattern_groups = {}
    for student_id in major_students:
        pattern = student_patterns.get(student_id, "未知型")
        if pattern not in pattern_groups:
            pattern_groups[pattern] = []
        pattern_groups[pattern].append(student_id)
    
    # 每个学习模式只选择一个代表性学生
    sampled = []
    for pattern, students in pattern_groups.items():
        # 随机选择一个学生作为该学习模式的代表
        sampled.append(random.choice(students))
    
    return sampled


def batch_calculate_learning_patterns(student_ids: List[str], 
                                       submit_records: pd.DataFrame) -> Dict[str, str]:
    """批量计算学生学习模式（优化性能）"""
    patterns = {}
    
    # 一次性计算所有学生的统计信息
    student_stats = submit_records[submit_records['student_ID'].isin(student_ids)].groupby('student_ID').agg({
        'title_ID': ['count', 'nunique']
    }).reset_index()
    
    student_stats.columns = ['student_ID', 'total_submits', 'unique_titles']
    
    for _, row in student_stats.iterrows():
        student_id = row['student_ID']
        unique_titles = row['unique_titles']
        total_submits = row['total_submits']
        repeat_rate = total_submits / unique_titles if unique_titles > 0 else 0
        
        if repeat_rate > 3:
            patterns[student_id] = "反复练习型"
        elif unique_titles > 30:
            patterns[student_id] = "探索尝试型"
        else:
            patterns[student_id] = "稳步推进型"
    
    # 为没有提交记录的学生设置默认值
    for student_id in student_ids:
        if student_id not in patterns:
            patterns[student_id] = "未知型"
    
    return patterns


def build_sankey_data() -> Dict[str, Any]:
    """构建桑基图数据"""
    # 加载数据
    title_info = load_title_info()
    student_info = load_student_info()
    submit_records = load_submit_records()
    individual_knowledge = load_individual_knowledge_mastery()
    individual_title = load_individual_title_mastery()
    major_knowledge = load_major_knowledge_mastery()
    
    nodes = []
    links = []
    
    # ========== 第一级：主知识点节点 ==========
    knowledge_nodes = {}
    all_knowledges = title_info['knowledge'].dropna().unique()
    
    for knowledge in all_knowledges:
        # 计算该知识点相关题目总量
        knowledge_titles = title_info[title_info['knowledge'] == knowledge]
        title_count = len(knowledge_titles)
        total_score = knowledge_titles['score'].sum() if 'score' in knowledge_titles.columns else 0
        
        # 计算平均掌握度（所有学生）
        knowledge_mastery = individual_knowledge[individual_knowledge['knowledge'] == knowledge]
        avg_mastery = knowledge_mastery['knowledge_mastery_score'].mean() * 100 if not knowledge_mastery.empty else 0.0
        
        node_id = f"k_{knowledge}"
        knowledge_nodes[knowledge] = node_id
        
        nodes.append({
            "id": node_id,
            "category": 0,
            "length_param": title_count,
            "extra": f"平均掌握度：{avg_mastery:.1f}%、关联题目数：{title_count}道、总分值：{int(total_score)}分"
        })
    
    # ========== 第二级：专业群体节点 ==========
    major_nodes = {}
    all_majors = student_info['major'].dropna().unique()
    
    # 计算专业人数
    major_counts = student_info['major'].value_counts().to_dict()
    
    # 计算专业平均掌握度
    major_avg_mastery = {}
    for major in all_majors:
        major_students = student_info[student_info['major'] == major]['student_ID'].tolist()
        major_knowledge_data = individual_knowledge[individual_knowledge['student_ID'].isin(major_students)]
        if not major_knowledge_data.empty:
            major_avg_mastery[major] = major_knowledge_data['knowledge_mastery_score'].mean() * 100
        else:
            major_avg_mastery[major] = 0.0
    
    # 计算专业提交总量
    major_submit_counts = {}
    for major in all_majors:
        major_students = student_info[student_info['major'] == major]['student_ID'].tolist()
        major_submits = submit_records[submit_records['student_ID'].isin(major_students)]
        major_submit_counts[major] = len(major_submits)
    
    for major in all_majors:
        node_id = f"m_{major}"
        major_nodes[major] = node_id
        major_name = get_major_name(major)
        major_category = get_major_category(major)
        
        nodes.append({
            "id": node_id,
            "name": major_name,  # 添加专业名称显示
            "category": 1,
            "length_param": major_counts.get(major, 0),
            "extra": f"专业类别：{major_category}、专业人数：{major_counts.get(major, 0)}人、平均掌握度：{major_avg_mastery.get(major, 0.0):.1f}%、提交总量：{major_submit_counts.get(major, 0)}次"
        })
    
    # ========== 链路1：主知识点→专业 ==========
    for knowledge in all_knowledges:
        knowledge_id = knowledge_nodes[knowledge]
        
        for major in all_majors:
            major_id = major_nodes[major]
            
            # 获取该专业的学生
            major_students = student_info[student_info['major'] == major]['student_ID'].tolist()
            
            # 计算该专业对知识点相关题目的提交量
            knowledge_titles = title_info[title_info['knowledge'] == knowledge]['title_ID'].tolist()
            major_knowledge_submits = submit_records[
                (submit_records['student_ID'].isin(major_students)) &
                (submit_records['title_ID'].isin(knowledge_titles))
            ]
            submit_count = len(major_knowledge_submits)
            
            if submit_count > 0:
                # 计算该知识点总提交量
                all_knowledge_submits = submit_records[
                    submit_records['title_ID'].isin(knowledge_titles)
                ]
                total_knowledge_submits = len(all_knowledge_submits)
                submit_ratio = (submit_count / total_knowledge_submits * 100) if total_knowledge_submits > 0 else 0.0
                
                # 计算该专业在该知识点的平均掌握度
                major_knowledge_data = major_knowledge[major_knowledge['major'] == major]
                major_knowledge_data = major_knowledge_data[major_knowledge_data['knowledge'] == knowledge]
                major_avg = major_knowledge_data['knowledge_mastery_score'].mean() * 100 if not major_knowledge_data.empty else 0.0
                
                links.append({
                    "source": knowledge_id,
                    "target": major_id,
                    "value": submit_count,
                    "extra": f"提交量占该知识点总提交量比例：{submit_ratio:.1f}%、该专业平均掌握度：{major_avg:.1f}%"
                })
    
    # ========== 预计算所有学生的学习模式（批量优化） ==========
    all_student_ids = student_info['student_ID'].tolist()
    student_patterns = batch_calculate_learning_patterns(all_student_ids, submit_records)
    
    # ========== 第三级：学生个体节点（每个专业-学习模式组合唯一） ==========
    student_nodes = {}  # 完整student_id -> 节点ID的映射
    sampled_students_by_major = {}
    student_counter = 0
    
    for major in all_majors:
        sampled_students = get_unique_pattern_students(major, student_info, submit_records, title_info, student_patterns)
        sampled_students_by_major[major] = sampled_students
    
    # 收集所有被抽样的学生ID
    all_sampled_students = []
    for students in sampled_students_by_major.values():
        all_sampled_students.extend(students)
    
    # 批量计算所有抽样学生的统计信息
    student_stats = batch_calculate_student_stats(all_sampled_students, individual_knowledge, submit_records)
    
    # 创建学生节点
    for major in all_majors:
        sampled_students = sampled_students_by_major[major]
        
        for student_id in sampled_students:
            student_counter += 1
            node_id = f"s_{student_counter:03d}"  # 使用序号确保唯一性
            student_nodes[student_id] = node_id
            
            # 使用预计算的统计信息
            stats = student_stats.get(student_id, {'overall_mastery': 0.0, 'accuracy': 0.0, 'total_submits': 0})
            learning_pattern = student_patterns.get(student_id, "未知型")
            
            major_name = get_major_name(major)
            nodes.append({
                "id": node_id,
                "category": 2,
                "extra": f"专业：{major_name}、学习模式：{learning_pattern}、个人综合掌握度：{stats['overall_mastery']:.1f}%、正确率：{stats['accuracy']:.1f}%、总提交次数：{stats['total_submits']}次"
            })
    
    # ========== 链路2：专业→学生 ==========
    for major in all_majors:
        major_id = major_nodes[major]
        sampled_students = sampled_students_by_major.get(major, [])
        
        for student_id in sampled_students:
            student_node_id = student_nodes.get(student_id)
            if student_node_id:
                major_name = get_major_name(major)
                links.append({
                    "source": major_id,
                    "target": student_node_id,
                    "value": 1,  # 固定值，前端控制链路均匀
                    "extra": f"学生专业：{major_name}、匹配度：100%"
                })
    
    # ========== 第四级：题目节点 ==========
    question_nodes = {}
    all_titles = title_info['title_ID'].dropna().unique()
    question_counter = 0
    
    for title_id in all_titles:
        question_counter += 1
        title_row = title_info[title_info['title_ID'] == title_id].iloc[0]
        knowledge = title_row['knowledge']
        score = title_row.get('score', 0)
        
        # 使用完整的title_id确保唯一性，但显示时简化
        node_id = f"q_{question_counter:02d}"  # 使用序号确保唯一
        question_nodes[title_id] = node_id
        
        # 计算题目综合效率（简化：使用平均掌握度）
        title_mastery = individual_title[individual_title['title_ID'] == title_id]
        avg_efficiency = title_mastery['title_mastery_score'].mean() * 100 if not title_mastery.empty else 0.0
        
        knowledge_id = knowledge_nodes.get(knowledge, f"k_{knowledge}")
        
        nodes.append({
            "id": node_id,
            "name": f"Q{question_counter}（{knowledge}）",
            "category": 3,
            "length_param": int(score) if pd.notna(score) else 0,
            "extra": f"所属知识点：{knowledge_id}、题目分值：{int(score)}分、综合效率：{avg_efficiency:.1f}%"
        })
    
    # ========== 链路3：学生→题目 ==========
    for major in all_majors:
        sampled_students = sampled_students_by_major.get(major, [])
        
        for student_id in sampled_students:
            student_node_id = student_nodes.get(student_id)
            if not student_node_id:
                continue
            
            # 获取该学生的提交记录
            student_submits = submit_records[submit_records['student_ID'] == student_id]
            
            # 统计学生对每个题目的提交次数
            title_submit_counts = student_submits['title_ID'].value_counts().to_dict()
            
            for title_id, submit_count in title_submit_counts.items():
                if title_id in question_nodes:
                    question_node_id = question_nodes[title_id]
                    
                    # 计算正确次数和正确率
                    title_submits = student_submits[student_submits['title_ID'] == title_id]
                    if 'state' in title_submits.columns:
                        correct_count = len(title_submits[title_submits['state'] == 'Absolutely_Correct'])
                        accuracy = (correct_count / submit_count * 100) if submit_count > 0 else 0.0
                    else:
                        correct_count = 0
                        accuracy = 0.0
                    
                    # 计算最高得分
                    if 'score' in title_submits.columns:
                        max_score = title_submits['score'].max() if not title_submits.empty else 0
                    else:
                        max_score = 0
                    
                    links.append({
                        "source": student_node_id,
                        "target": question_node_id,
                        "value": submit_count,
                        "extra": f"正确次数：{correct_count}次、正确率：{accuracy:.1f}%、最高得分：{int(max_score)}分"
                    })
    
    # ========== 反向关联链路 ==========
    # 反向链路1：题目→学生（反向）
    for major in all_majors:
        sampled_students = sampled_students_by_major.get(major, [])
        
        for student_id in sampled_students:
            student_node_id = student_nodes.get(student_id)
            if not student_node_id:
                continue
            
            # 获取该学生的提交记录
            student_submits = submit_records[submit_records['student_ID'] == student_id]
            
            # 统计学生对每个题目的提交次数
            title_submit_counts = student_submits['title_ID'].value_counts().to_dict()
            
            for title_id, submit_count in title_submit_counts.items():
                if title_id in question_nodes:
                    question_node_id = question_nodes[title_id]
                    
                    # 反向链路：题目→学生
                    links.append({
                        "source": question_node_id,
                        "target": student_node_id,
                        "value": submit_count,
                        "extra": f"反向关联：该题目被该学生提交{submit_count}次"
                    })
    
    # 反向链路2：学生→专业（反向）
    for major in all_majors:
        major_id = major_nodes[major]
        sampled_students = sampled_students_by_major.get(major, [])
        major_name = get_major_name(major)
        
        for student_id in sampled_students:
            student_node_id = student_nodes.get(student_id)
            if student_node_id:
                # 反向链路：学生→专业
                links.append({
                    "source": student_node_id,
                    "target": major_id,
                    "value": 1,  # 固定值，与正向链路保持一致
                    "extra": f"反向关联：该学生属于{major_name}专业"
                })
    
    # 反向链路3：专业→知识点（反向）
    for knowledge in all_knowledges:
        knowledge_id = knowledge_nodes[knowledge]
        
        for major in all_majors:
            major_id = major_nodes[major]
            
            # 获取该专业的学生
            major_students = student_info[student_info['major'] == major]['student_ID'].tolist()
            
            # 计算该专业对知识点相关题目的提交量
            knowledge_titles = title_info[title_info['knowledge'] == knowledge]['title_ID'].tolist()
            major_knowledge_submits = submit_records[
                (submit_records['student_ID'].isin(major_students)) &
                (submit_records['title_ID'].isin(knowledge_titles))
            ]
            submit_count = len(major_knowledge_submits)
            
            if submit_count > 0:
                major_name = get_major_name(major)
                # 反向链路：专业→知识点
                links.append({
                    "source": major_id,
                    "target": knowledge_id,
                    "value": submit_count,
                    "extra": f"反向关联：{major_name}专业在该知识点提交{submit_count}次"
                })
    
    return {
        "nodes": nodes,
        "links": links
    }


@green_top_bp.route('/sankey', methods=['GET'])
def get_sankey():
    """获取桑基图数据"""
    try:
        data = build_sankey_data()
        return jsonify(data)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500
