from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import pandas as pd
import os
import json
from datetime import datetime
from typing import Optional

from pink_views import pink_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(pink_bp)

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

@app.route('/api/classes', methods=['GET'])
def get_classes():
    """获取所有班级列表"""
    df = pd.read_csv(STUDENT_INFO_FILE)
    classes = sorted(df['major'].unique().tolist())
    return jsonify(classes)

@app.route('/api/students', methods=['GET'])
def get_students():
    """获取所有学生列表"""
    df = pd.read_csv(STUDENT_INFO_FILE)
    students = df[['student_ID', 'major']].to_dict('records')
    return jsonify(students)

@app.route('/api/students/<class_name>', methods=['GET'])
def get_students_by_class(class_name):
    """根据班级获取学生列表"""
    df = pd.read_csv(STUDENT_INFO_FILE)
    students = df[df['major'] == class_name][['student_ID', 'major']].to_dict('records')
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