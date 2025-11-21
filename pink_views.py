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
    y_titles = sorted(title_df['title_ID'].dropna().unique().tolist())
    y_labels = [alias_map.get(t, t) for t in y_titles]
    knowledge_index = {label: idx for idx, label in enumerate(x_labels)}
    title_index = {title: idx for idx, title in enumerate(y_titles)}

    heatmap_rows: List[List[Any]] = []
    for _, row in title_df.iterrows():
        title_id = row['title_ID']
        knowledge = row['knowledge']
        sub_knowledge = row.get('sub_knowledge', '')
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
            sub_knowledge,
            match_index,
            correct_rate,
            discrimination
        ])

    return {
        'heatedConfig': {
            'xAxisLabels': x_labels,
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

    merged = submit_df.merge(title_df, on='title_ID', how='left')
    merged['timeconsume'] = pd.to_numeric(merged['timeconsume'], errors='coerce')
    merged['memory'] = pd.to_numeric(merged['memory'], errors='coerce')

    agg = (
        merged.groupby('title_ID')
        .agg(
            knowledge=('knowledge', 'first'),
            title_score=('title_score', 'first'),
            submission_count=('title_ID', 'count'),
            avg_timeconsume=('timeconsume', lambda x: pd.Series(x).mean(skipna=True)),
            avg_memory=('memory', lambda x: pd.Series(x).mean(skipna=True))
        )
        .reset_index()
    )

    overall_time = agg['avg_timeconsume'].mean() or 1
    overall_memory = agg['avg_memory'].mean() or 1

    def ratio(value: float, baseline: float) -> float:
        if baseline == 0:
            return 0.0
        return round((float(value) / baseline) * 100, 1)

    bubble_data = []
    for _, row in agg.iterrows():
        time_eff = ratio(row['avg_timeconsume'], overall_time)
        memory_eff = ratio(row['avg_memory'], overall_memory)
        comp_eff = round((time_eff + memory_eff) / 2, 1)
        bubble_data.append({
            'title_ID': row['title_ID'],
            'knowledge': row['knowledge'],
            'score': int(row['title_score']) if pd.notna(row['title_score']) else None,
            'submission_count': int(row['submission_count']),
            'timeconsume': round(float(row['avg_timeconsume']), 2) if pd.notna(row['avg_timeconsume']) else None,
            'memory': round(float(row['avg_memory']), 2) if pd.notna(row['avg_memory']) else None,
            'times_efficiency': time_eff,
            'ram_efficiency': memory_eff,
            'comprehensive_efficiency': comp_eff
        })

    x_labels = sorted([label for label in title_df['knowledge'].dropna().unique().tolist()])
    return {
        'bubbleData': bubble_data,
        'xAxisLabels': x_labels
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
    if records.empty:
        return {'dimensionData': {'time': {}, 'knowledge': {}, 'method': {}}}

    title_meta = load_title_info()[['title_ID', 'knowledge']].drop_duplicates(subset=['title_ID'])
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
        week_labels = {wk: f"第{i + 1}周({wk.strftime('%Y-%m-%d')})" for i, wk in enumerate(unique_weeks)}
        time_df['time_bucket'] = time_df['week_start'].map(week_labels)
        ordered_time_labels = [week_labels[wk] for wk in unique_weeks]
        time_section = _build_state_series(time_df, 'time_bucket', ordered_time_labels)
    else:
        time_section = {'xLabels': [], 'stateData': []}

    knowledge_df = merged.dropna(subset=['knowledge']).copy()
    knowledge_labels = sorted(knowledge_df['knowledge'].unique().tolist())
    knowledge_section = _build_state_series(knowledge_df, 'knowledge', knowledge_labels)

    method_df = merged.dropna(subset=['method']).copy()
    method_labels = sorted(method_df['method'].unique().tolist())
    method_section = _build_state_series(method_df, 'method', method_labels)

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

