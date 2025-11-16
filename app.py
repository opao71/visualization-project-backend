from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# 数据文件路径
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
STUDENT_INFO_FILE = os.path.join(DATA_DIR, 'Data_StudentInfo.csv')
CLASS_TITLE_MASTERY = os.path.join(DATA_DIR, 'mastery', 'class_title_mastery.csv')
INDIVIDUAL_TITLE_MASTERY = os.path.join(DATA_DIR, 'mastery', 'individual_title_mastery.csv')

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)