from flask import Blueprint, jsonify, request
import os
from typing import Optional

from learner_profile import LearnerProfileAnalyzer


green_bottom_bp = Blueprint('green_bottom', __name__, url_prefix='/api')

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')

# 独立的 LearnerProfileAnalyzer 实例（与 app.py 中的逻辑保持一致）
profile_analyzer = LearnerProfileAnalyzer(DATA_DIR)


@green_bottom_bp.route('/knowledge/mastery-trend', methods=['GET'])
def get_knowledge_mastery_trend():
    """
    获取知识点掌握度趋势数据（绿色框2 - 知识点掌握度折线图）

    路径: GET /api/knowledge/mastery-trend
    """
    try:
        student_id = request.args.get('student_id')
        class_name = request.args.get('class_name')
        start_month = request.args.get('start_month')
        end_month = request.args.get('end_month')
        top_k = int(request.args.get('top_k', 4))

        # knowledge_ids 支持两种方式：
        # 1) knowledge_ids=kid1,kid2
        # 2) knowledge_ids=kid1&knowledge_ids=kid2
        knowledge_ids_param = request.args.get('knowledge_ids')
        if knowledge_ids_param:
            knowledge_ids = [kid.strip() for kid in knowledge_ids_param.split(',') if kid.strip()]
        else:
            knowledge_ids = request.args.getlist('knowledge_ids') or None

        if not student_id:
            return jsonify({'error': 'student_id参数必填', 'code': 'INVALID_PARAMETER'}), 400

        result = profile_analyzer.get_knowledge_mastery_trend(
            student_id=student_id,
            class_name=class_name,
            start_month=start_month,
            end_month=end_month,
            top_k=top_k,
            knowledge_ids=knowledge_ids,
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'code': 'SERVER_ERROR'}), 500


