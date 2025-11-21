from flask import Blueprint, jsonify, request
import pandas as pd
import os
from functools import lru_cache
from typing import Dict, Any, List, Set

green_top_bp = Blueprint('green_top', __name__, url_prefix='/api/green/top')

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
MASTER_DIR = os.path.join(DATA_DIR, 'mastery')
SUBMIT_DIR = os.path.join(DATA_DIR, 'Data_SubmitRecord')

TITLE_INFO_FILE = os.path.join(DATA_DIR, 'Data_TitleInfo.csv')
INDIVIDUAL_TITLE_FILE = os.path.join(MASTER_DIR, 'individual_title_mastery.csv')
INDIVIDUAL_SUB_FILE = os.path.join(MASTER_DIR, 'individual_sub_knowledge_mastery.csv')


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
def load_title_info() -> pd.DataFrame:
    df = pd.read_csv(TITLE_INFO_FILE, encoding='utf-8-sig')
    df = _normalize_columns(df)
    for col in ['title_ID', 'knowledge', 'sub_knowledge']:
        df = _normalize_column_name(df, col)
    return df[['title_ID', 'knowledge', 'sub_knowledge']].drop_duplicates()


@lru_cache(maxsize=1)
def load_individual_title_mastery() -> pd.DataFrame:
    df = pd.read_csv(INDIVIDUAL_TITLE_FILE)
    df = _normalize_columns(df)
    return df


@lru_cache(maxsize=1)
def load_individual_sub_mastery() -> pd.DataFrame:
    df = pd.read_csv(INDIVIDUAL_SUB_FILE)
    df = _normalize_columns(df)
    df = _normalize_column_name(df, 'sub_knowledge')
    df = _normalize_column_name(df, 'knowledge_mastery_score')
    return df


def _split_knowledge(sub_code: str) -> str:
    if not isinstance(sub_code, str):
        return ''
    return sub_code.split('_')[0]


def _get_class_student_ids(class_name: str) -> Set[str]:
    filename = f'SubmitRecord-{class_name}.csv'
    path = os.path.join(SUBMIT_DIR, filename)
    if not os.path.exists(path):
        return set()
    df = pd.read_csv(path)
    if 'student_ID' not in df.columns:
        return set()
    return set(df['student_ID'].dropna().astype(str).tolist())


def build_sunburst_payload(class_name: str, student_id: str) -> Dict[str, Any]:
    title_info = load_title_info()
    title_mastery = load_individual_title_mastery()
    student_titles = title_mastery[title_mastery['student_ID'] == student_id].copy()
    if student_titles.empty:
        raise ValueError('未找到该学生的题目掌握数据')
    student_titles = student_titles.merge(title_info, on='title_ID', how='left')

    sub_mastery = load_individual_sub_mastery()
    student_sub = sub_mastery[sub_mastery['student_ID'] == student_id].copy()
    student_sub['knowledge'] = student_sub['sub_knowledge'].apply(_split_knowledge)

    knowledge_from_titles = (
        student_titles.groupby('knowledge')['title_mastery_score']
        .mean()
        .dropna()
        .to_dict()
    )
    knowledge_from_sub = (
        student_sub.groupby('knowledge')['knowledge_mastery_score']
        .mean()
        .dropna()
        .to_dict()
        if not student_sub.empty else {}
    )

    knowledge_keys = set(knowledge_from_titles.keys()) | set(knowledge_from_sub.keys())

    hierarchy_children: List[Dict[str, Any]] = []
    for knowledge in sorted(knowledge_keys):
        knowledge_mastery = knowledge_from_sub.get(
            knowledge,
            knowledge_from_titles.get(knowledge, 0.0)
        )
        knowledge_node = {
            'name': knowledge,
            'mastery': round(float(knowledge_mastery), 4) if pd.notna(knowledge_mastery) else None,
            'children': [],
            'value': 0
        }

        sub_rows = student_sub[student_sub['knowledge'] == knowledge]
        if sub_rows.empty:
            sub_rows = pd.DataFrame()

        for _, sub_row in sub_rows.iterrows():
            sub_code = sub_row['sub_knowledge']
            sub_node = {
                'name': sub_code,
                'mastery': round(float(sub_row['knowledge_mastery_score']), 4),
                'children': [],
                'value': 0
            }
            question_rows = student_titles[student_titles['sub_knowledge'] == sub_code]
            for _, q_row in question_rows.iterrows():
                sub_node['children'].append({
                    'name': q_row['title_ID'],
                    'mastery': round(float(q_row['title_mastery_score']), 4),
                    'value': 1
                })
            if not sub_node['children']:
                # fallback: attach questions by knowledge only
                fallback_rows = student_titles[student_titles['knowledge'] == knowledge]
                for _, q_row in fallback_rows.iterrows():
                    sub_node['children'].append({
                        'name': q_row['title_ID'],
                        'mastery': round(float(q_row['title_mastery_score']), 4),
                        'value': 1
                    })
                    sub_node['value'] += 1
                if not fallback_rows.empty:
                    knowledge_node['value'] += len(fallback_rows)
            else:
                sub_node['value'] = len(sub_node['children'])
                knowledge_node['value'] += sub_node['value']
            knowledge_node['children'].append(sub_node)

        if not knowledge_node['children']:
            question_rows = student_titles[student_titles['knowledge'] == knowledge]
            for _, q_row in question_rows.iterrows():
                knowledge_node['children'].append({
                    'name': q_row['title_ID'],
                    'mastery': round(float(q_row['title_mastery_score']), 4),
                    'value': 1
                })
                knowledge_node['value'] += 1

        hierarchy_children.append(knowledge_node)

    return {
        'class': class_name,
        'student': student_id,
        'sunburst': {
            'name': '知识体系',
            'children': hierarchy_children
        }
    }


def build_sunburst_batch_payload(class_name: str) -> Dict[str, Any]:
    student_ids = _get_class_student_ids(class_name)
    if not student_ids:
        raise ValueError('未找到该班级的学生数据')

    results = []
    for sid in sorted(student_ids):
        try:
            payload = build_sunburst_payload(class_name, sid)
            results.append({
                'student_ID': sid,
                'sunburst': payload['sunburst']
            })
        except ValueError:
            continue
    if not results:
        raise ValueError('该班级没有可用的学生掌握数据')
    return {
        'class': class_name,
        'students': results
    }


def _required_params() -> Dict[str, str]:
    class_name = request.args.get('class')
    student_id = request.args.get('student_ID')
    if not class_name or not student_id:
        raise ValueError('需要提供 class 和 student_ID 参数')
    return {'class': class_name, 'student': student_id}


@green_top_bp.route('/sunburst', methods=['GET'])
def get_green_sunburst():
    try:
        params = _required_params()
        payload = build_sunburst_payload(params['class'], params['student'])
        return jsonify(payload)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@green_top_bp.route('/sunburst/batch', methods=['GET'])
def get_green_sunburst_batch():
    try:
        class_name = request.args.get('class')
        if not class_name:
            raise ValueError('需要提供 class 参数')
        payload = build_sunburst_batch_payload(class_name)
        return jsonify(payload)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500



