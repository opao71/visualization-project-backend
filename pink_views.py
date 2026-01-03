from flask import Blueprint, jsonify
import pandas as pd
import os
from functools import lru_cache
from typing import List, Dict, Any
import glob


pink_bp = Blueprint('pink', __name__, url_prefix='/api/pink')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TITLE_INFO_FILE = os.path.join(DATA_DIR, 'Data_TitleInfo.csv')
SUBMIT_RECORD_DIR = os.path.join(DATA_DIR, 'Data_SubmitRecord')
CLASS_TITLE_MASTERY = os.path.join(DATA_DIR, 'mastery', 'class_title_mastery.csv')
ALLOWED_STATES = {
    'Absolutely_Correct',
    'Absolutely_Error',
    'Partially_Correct',
    'Error1', 'Error2', 'Error3', 'Error4', 'Error5', 'Error6', 'Error7', 'Error8', 'Error9'
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.astype(str)
        .str.replace('\ufeff', '', regex=False)
        .str.strip()
    )
    return df


def _normalize_column_name(df: pd.DataFrame, target: str) -> pd.DataFrame:
    if target in df.columns:
        return df
    matches = [col for col in df.columns if col.lower() == target.lower()]
    if matches:
        df = df.rename(columns={matches[0]: target})
    return df


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
        # 可以根据实际数据添加更多映射
    }
    return knowledge_name_map.get(knowledge_code, f"知识点{knowledge_code}")


def get_method_name(method_code: str) -> str:
    """将编程方法编码转换为方法名称"""
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


def get_sub_knowledge_name(sub_knowledge_code: str) -> str:
    """将子知识点编码转换为子知识点名称"""
    if not sub_knowledge_code or pd.isna(sub_knowledge_code) or sub_knowledge_code == '':
        return '无'
    
    # 提取子知识点编码的前5个字符作为主要标识
    code = sub_knowledge_code.split('_')[0][:5] if '_' in sub_knowledge_code else sub_knowledge_code[:5]
    
    # 子知识点编码到名称的映射
    sub_knowledge_map = {
        't5V9e': '递归算法',
        'e1k6c': '贪心算法',
        'p8H2w': '动态规划',
        'd3F7k': '排序算法',
        'w9L4m': '搜索算法',
        'q2N8v': '图算法',
        # 可以根据实际数据添加更多映射
    }
    
    # 尝试匹配
    if code in sub_knowledge_map:
        return sub_knowledge_map[code]
    else:
        # 如果找不到映射，返回格式化的编码
        return f"子知识点{code}"


@lru_cache(maxsize=1)
def load_title_info() -> pd.DataFrame:
    df = pd.read_csv(TITLE_INFO_FILE, encoding='utf-8-sig')
    df = _normalize_columns(df)
    for col in ['title_ID', 'knowledge', 'sub_knowledge', 'score']:
        df = _normalize_column_name(df, col)

    if 'score' not in df.columns:
        df['score'] = 1

    for col in ['title_ID', 'knowledge', 'sub_knowledge']:
        if col not in df.columns:
            df[col] = ''
        df[col] = df[col].astype(str).str.replace('\ufeff', '', regex=False).str.strip()

    df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0)
    return df[['title_ID', 'score', 'knowledge', 'sub_knowledge']].drop_duplicates()


@lru_cache(maxsize=1)
def load_title_alias_map() -> Dict[str, str]:
    titles = sorted(load_title_info()['title_ID'].dropna().unique().tolist())
    return {title: f"Q_{idx + 1:02d}" for idx, title in enumerate(titles)}


@lru_cache(maxsize=1)
def load_submit_records() -> pd.DataFrame:
    csv_files = glob.glob(os.path.join(SUBMIT_RECORD_DIR, 'SubmitRecord-Class*.csv'))
    if not csv_files:
        columns = ['class', 'time', 'state', 'score', 'title_ID', 'method', 'memory', 'timeconsume', 'student_ID']
        return pd.DataFrame(columns=columns)
    frames = []
    for path in csv_files:
        df = pd.read_csv(path, encoding='utf-8-sig')
        df = _normalize_columns(df)
        for col in ['class', 'time', 'state', 'score', 'title_ID', 'method', 'memory', 'timeconsume', 'student_ID']:
            df = _normalize_column_name(df, col)
        frames.append(df[['class', 'time', 'state', 'score', 'title_ID', 'method', 'memory', 'timeconsume', 'student_ID']])
    merged = pd.concat(frames, ignore_index=True)
    merged['score'] = pd.to_numeric(merged['score'], errors='coerce').fillna(0)
    return merged


@lru_cache(maxsize=1)
def load_title_metrics() -> pd.DataFrame:
    df = pd.read_csv(CLASS_TITLE_MASTERY)
    grouped = (
        df.groupby('title_ID')
        .agg({
            'score_rate': 'mean',
            'score_rate_norm': 'mean',
            'title_mastery_score': 'mean'
        })
        .reset_index()
    )
    grouped['match_index'] = grouped['score_rate_norm'].apply(
        lambda x: int(max(1, min(10, round(float(x) * 10))))
    )
    grouped['correct_rate'] = grouped['score_rate'].apply(lambda x: round(float(x) * 100, 1))
    grouped['discrimination'] = grouped['title_mastery_score'].apply(lambda x: round(float(x), 2))
    return grouped[['title_ID', 'match_index', 'correct_rate', 'discrimination']]


def build_heatmap_payload() -> Dict[str, Any]:
    title_df = load_title_info()
    alias_map = load_title_alias_map()
    metrics_df = load_title_metrics().set_index('title_ID')
    x_labels = sorted(title_df['knowledge'].dropna().unique().tolist())
    # 创建知识点编码到名称的映射
    x_labels_display = [get_knowledge_name(code) for code in x_labels]  # 用于前端显示
    
    y_titles = sorted(title_df['title_ID'].dropna().unique().tolist())
    y_labels = [alias_map.get(t, t) for t in y_titles]
    knowledge_index = {label: idx for idx, label in enumerate(x_labels)}
    title_index = {title: idx for idx, title in enumerate(y_titles)}

    heatmap_rows: List[List[Any]] = []
    for _, row in title_df.iterrows():
        title_id = row['title_ID']
        knowledge = row['knowledge']
        sub_knowledge = row.get('sub_knowledge', '')
        sub_knowledge_name = get_sub_knowledge_name(sub_knowledge)  # 转换子知识点名称
        metric_row = metrics_df.loc[title_id] if title_id in metrics_df.index else None
        match_index = int(metric_row['match_index']) if metric_row is not None else 0
        correct_rate = float(metric_row['correct_rate']) if metric_row is not None else 0.0
        discrimination = float(metric_row['discrimination']) if metric_row is not None else 0.0

        heatmap_rows.append([
            knowledge_index.get(knowledge, 0),
            title_index.get(title_id, 0),
            alias_map.get(title_id, title_id),
            title_id,
            knowledge,
            sub_knowledge_name,  # 使用子知识点名称而不是编码
            match_index,
            correct_rate,
            discrimination
        ])

    return {
        'heatedConfig': {
            'xAxisLabels': x_labels_display,  # 返回知识点名称用于显示
            'xAxisLabelsCode': x_labels,  # 保留原始编码用于后端查询
            'yAxisLabels': y_labels
        },
        'heatmapCoreData': heatmap_rows
    }


def build_bubble_payload() -> Dict[str, Any]:
    title_df = load_title_info()[['title_ID', 'knowledge', 'score']].drop_duplicates(subset=['title_ID'])
    title_df = title_df.rename(columns={'score': 'title_score'})
    submit_df = load_submit_records()
    if submit_df.empty:
        return {'bubbleData': [], 'xAxisLabels': []}

    # 使用右连接确保包含所有题目，即使没有提交记录
    merged = title_df.merge(submit_df, on='title_ID', how='left')
    merged['timeconsume'] = pd.to_numeric(merged['timeconsume'], errors='coerce')
    merged['memory'] = pd.to_numeric(merged['memory'], errors='coerce')

    agg = (
        merged.groupby('title_ID')
        .agg(
            knowledge=('knowledge', 'first'),
            title_score=('title_score', 'first'),
            submission_count=('title_ID', lambda x: x.notna().sum()),
            avg_timeconsume=('timeconsume', lambda x: pd.Series(x).mean(skipna=True)),
            avg_memory=('memory', lambda x: pd.Series(x).mean(skipna=True))
        )
        .reset_index()
    )

    # 只计算有提交记录的题目的平均值
    valid_time = agg['avg_timeconsume'].dropna()
    valid_memory = agg['avg_memory'].dropna()
    overall_time = valid_time.mean() if not valid_time.empty else 1
    overall_memory = valid_memory.mean() if not valid_memory.empty else 1

    def ratio(baseline: float, value: float) -> float:
        if pd.isna(value) or value == 0:
            return 0.0
        return round((float(baseline) / float(value)) * 100, 1)

    # 获取题目别名映射
    alias_map = load_title_alias_map()
    
    bubble_data = []
    for _, row in agg.iterrows():
        time_eff = ratio(overall_time, row['avg_timeconsume']) if pd.notna(row['avg_timeconsume']) else 0.0
        memory_eff = ratio(overall_memory, row['avg_memory']) if pd.notna(row['avg_memory']) else 0.0
        comp_eff = round((time_eff + memory_eff) / 2, 1) if (time_eff > 0 or memory_eff > 0) else 0.0
        
        title_id = row['title_ID']
        knowledge_code = row['knowledge']
        bubble_data.append({
            'title_ID': alias_map.get(title_id, title_id),  # 使用题目别名
            'knowledge': knowledge_code,
            'knowledge_name': get_knowledge_name(knowledge_code),  # 添加知识点名称
            'score': int(row['title_score']) if pd.notna(row['title_score']) else None,
            'submission_count': int(row['submission_count']),
            'timeconsume': round(float(row['avg_timeconsume']), 2) if pd.notna(row['avg_timeconsume']) else None,
            'memory': round(float(row['avg_memory']), 2) if pd.notna(row['avg_memory']) else None,
            'times_efficiency': time_eff,
            'ram_efficiency': memory_eff,
            'comprehensive_efficiency': comp_eff
        })

    x_labels = sorted([label for label in title_df['knowledge'].dropna().unique().tolist()])
    # 创建知识点编码到名称的映射
    x_labels_display = [get_knowledge_name(code) for code in x_labels]  # 用于前端显示
    
    return {
        'bubbleData': bubble_data,
        'xAxisLabels': x_labels_display,  # 返回知识点名称用于显示
        'xAxisLabelsCode': x_labels  # 保留原始编码用于后端查询
    }


def _build_state_series(df: pd.DataFrame, group_col: str, labels: List[str]) -> Dict[str, Any]:
    if not labels:
        return {'xLabels': [], 'stateData': []}
    states = sorted(df['state'].dropna().unique().tolist())
    if not states:
        return {'xLabels': labels, 'stateData': []}
    counts = (
        df.groupby([group_col, 'state'])
        .size()
        .unstack(fill_value=0)
        .reindex(index=labels, columns=states, fill_value=0)
    )
    totals = counts.sum(axis=1).replace(0, 1)
    ratios = (counts.div(totals, axis=0) * 100).round(1)

    state_data = []
    for state in states:
        state_data.append({
            'stateCode': state,
            'ratios': [float(ratios.loc[label, state]) for label in labels]
        })
    return {'xLabels': labels, 'stateData': state_data}


def build_state_trends_payload() -> Dict[str, Any]:
    records = load_submit_records()
    title_meta = load_title_info()[['title_ID', 'knowledge']].drop_duplicates(subset=['title_ID'])
    
    if records.empty:
        # 即使没有提交记录，也要返回知识点标签
        knowledge_labels = sorted(title_meta['knowledge'].dropna().unique().tolist())
        knowledge_labels_display = [get_knowledge_name(code) for code in knowledge_labels]  # 用于前端显示
        return {
            'dimensionData': {
                'time': {'xLabels': [], 'stateData': []},
                'knowledge': {'xLabels': knowledge_labels_display, 'stateData': []},
                'method': {'xLabels': [], 'stateData': []}
            }
        }

    merged = records.merge(title_meta, on='title_ID', how='left')
    merged['time_dt'] = pd.to_datetime(merged['time'], unit='s', errors='coerce')
    merged = merged.dropna(subset=['state'])
    merged['state'] = merged['state'].astype(str).str.strip()
    merged = merged[merged['state'].isin(ALLOWED_STATES)]

    time_section = {}
    time_df = merged.dropna(subset=['time_dt']).copy()
    if not time_df.empty:
        time_df['week_start'] = time_df['time_dt'].dt.to_period('W').dt.start_time
        unique_weeks = sorted(time_df['week_start'].dropna().unique().tolist())
        
        # 兼容不同 pandas 版本：确保所有元素都是 Timestamp 对象
        unique_weeks = [pd.Timestamp(wk) if not isinstance(wk, pd.Timestamp) else wk for wk in unique_weeks]

        week_labels = {wk: f"第{i + 1}周({wk.strftime('%Y-%m-%d')})" for i, wk in enumerate(unique_weeks)}
        time_df['time_bucket'] = time_df['week_start'].map(week_labels)
        ordered_time_labels = [week_labels[wk] for wk in unique_weeks]
        time_section = _build_state_series(time_df, 'time_bucket', ordered_time_labels)
    else:
        time_section = {'xLabels': [], 'stateData': []}

    knowledge_df = merged.dropna(subset=['knowledge']).copy()
    knowledge_labels = sorted(knowledge_df['knowledge'].unique().tolist())
    knowledge_section = _build_state_series(knowledge_df, 'knowledge', knowledge_labels)
    # 将xLabels替换为知识点名称
    knowledge_labels_display = [get_knowledge_name(code) for code in knowledge_labels]
    knowledge_section['xLabels'] = knowledge_labels_display

    method_df = merged.dropna(subset=['method']).copy()
    method_labels = sorted(method_df['method'].unique().tolist())
    method_section = _build_state_series(method_df, 'method', method_labels)
    # 将method的xLabels替换为友好的名称
    method_labels_display = [get_method_name(code) for code in method_labels]
    method_section['xLabels'] = method_labels_display

    return {
        'dimensionData': {
            'time': time_section,
            'knowledge': knowledge_section,
            'method': method_section
        }
    }


@pink_bp.route('/heatmap', methods=['GET'])
def get_heatmap_dataset():
    """粉色视图一：题目匹配热力图"""
    payload = build_heatmap_payload()
    return jsonify(payload)


@pink_bp.route('/bubbles', methods=['GET'])
def get_bubble_dataset():
    """粉色视图二：题目综合表现气泡图"""
    payload = build_bubble_payload()
    return jsonify(payload)


@pink_bp.route('/state-trends', methods=['GET'])
def get_state_trends():
    """粉色视图三：三维度答题状态折线图"""
    payload = build_state_trends_payload()
    return jsonify(payload)

