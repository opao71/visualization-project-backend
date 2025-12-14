"""
4.2 个性化学习行为模式 - 学习行为分析模块
实现特征提取、聚类分析和模式分类
"""
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import os
from collections import defaultdict

class LearningBehaviorAnalyzer:
    """学习行为分析器"""
    
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.student_info_file = os.path.join(data_dir, 'Data_StudentInfo.csv')
        self.title_info_file = os.path.join(data_dir, 'Data_TitleInfo.csv')
        self.submit_record_dir = os.path.join(data_dir, 'Data_SubmitRecord')
        
        # 缓存数据
        self._student_info = None
        self._title_info = None
        self._submit_records = {}
        
    def _load_student_info(self):
        """加载学生信息"""
        if self._student_info is None:
            self._student_info = pd.read_csv(self.student_info_file)
        return self._student_info
    
    def _load_title_info(self):
        """加载题目信息"""
        if self._title_info is None:
            self._title_info = pd.read_csv(self.title_info_file)
        return self._title_info
    
    def _load_submit_records(self, class_name=None):
        """加载提交记录"""
        if class_name:
            # 加载指定班级的数据
            class_num = class_name[-1] if class_name and class_name[-1].isdigit() else None
            if class_num and f'Class{class_num}' not in self._submit_records:
                file_path = os.path.join(self.submit_record_dir, f'SubmitRecord-Class{class_num}.csv')
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    # 添加datetime列
                    df['datetime'] = pd.to_datetime(df['time'], unit='s')
                    df['month'] = df['datetime'].dt.to_period('M').astype(str)
                    df['date'] = df['datetime'].dt.date
                    df['hour'] = df['datetime'].dt.hour
                    self._submit_records[f'Class{class_num}'] = df
            return self._submit_records.get(f'Class{class_num}', pd.DataFrame())
        else:
            # 加载所有班级的数据
            all_records = []
            for i in range(1, 16):
                class_key = f'Class{i}'
                if class_key not in self._submit_records:
                    file_path = os.path.join(self.submit_record_dir, f'SubmitRecord-Class{i}.csv')
                    if os.path.exists(file_path):
                        df = pd.read_csv(file_path)
                        df['datetime'] = pd.to_datetime(df['time'], unit='s')
                        df['month'] = df['datetime'].dt.to_period('M').astype(str)
                        df['date'] = df['datetime'].dt.date
                        df['hour'] = df['datetime'].dt.hour
                        self._submit_records[class_key] = df
                if class_key in self._submit_records:
                    all_records.append(self._submit_records[class_key])
            if all_records:
                return pd.concat(all_records, ignore_index=True)
            return pd.DataFrame()
    
    def _filter_data(self, df, student_id=None, class_name=None, month=None):
        """筛选数据"""
        if df.empty:
            return df
        
        # 按学生筛选
        if student_id:
            df = df[df['student_ID'] == student_id]
        
        # 按班级筛选
        if class_name:
            class_num = class_name[-1] if class_name and class_name[-1].isdigit() else None
            if class_num:
                df = df[df['class'] == f'Class{class_num}']
        
        # 按月份筛选
        if month:
            df = df[df['month'] == month]
        
        # 过滤有效记录（去除异常值）
        df = df[df['state'].isin(['Absolutely_Correct', 'Partially_Correct', 'Error1', 'Error2'])]
        
        return df
    
    def calculate_submit_count(self, df):
        """计算提交次数"""
        return len(df)
    
    def calculate_active_days(self, df):
        """计算活跃天数"""
        if df.empty:
            return 0
        return df['date'].nunique()
    
    def calculate_question_count(self, df):
        """计算答题数（不同题目数）"""
        if df.empty:
            return 0
        return df['title_ID'].nunique()
    
    def calculate_correct_ratio(self, df):
        """计算正确占比"""
        if df.empty:
            return 0.0
        correct_states = ['Absolutely_Correct', 'Partially_Correct']
        correct_count = len(df[df['state'].isin(correct_states)])
        return correct_count / len(df) if len(df) > 0 else 0.0
    
    def get_behavior_features(self, student_id=None, class_name=None, month=None):
        """
        获取学习行为特征
        
        参数:
            student_id: 学生ID（可选）
            class_name: 班级名称（可选）
            month: 月份（可选，格式：YYYY-MM）
        
        返回:
            dict: 包含submit_count, active_days, question_count, correct_ratio
        """
        # 加载数据
        if class_name:
            df = self._load_submit_records(class_name)
        else:
            df = self._load_submit_records()
        
        # 筛选数据
        df = self._filter_data(df, student_id, class_name, month)
        
        if df.empty:
            return {
                'submit_count': 0,
                'active_days': 0,
                'question_count': 0,
                'correct_ratio': 0.0
            }
        
        # 计算特征
        features = {
            'submit_count': self.calculate_submit_count(df),
            'active_days': self.calculate_active_days(df),
            'question_count': self.calculate_question_count(df),
            'correct_ratio': self.calculate_correct_ratio(df)
        }
        
        return features
    
    def get_all_students_features(self, class_name=None, month=None):
        """
        获取所有学生的特征（用于聚类分析）
        
        参数:
            class_name: 班级名称（可选）
            month: 月份（可选）
        
        返回:
            DataFrame: 包含所有学生的特征
        """
        # 加载数据
        if class_name:
            df = self._load_submit_records(class_name)
        else:
            df = self._load_submit_records()
        
        # 筛选数据
        df = self._filter_data(df, class_name=class_name, month=month)
        
        if df.empty:
            return pd.DataFrame()
        
        # 按学生分组计算特征
        student_features = []
        
        for student_id in df['student_ID'].unique():
            student_df = df[df['student_ID'] == student_id]
            
            # 聚合所有月份（按文档要求：按学习者聚合所有月份数据）
            # submit_count: 所有月份提交次数之和
            # active_days: 所有月份不重复日期集合
            # question_count: 所有月份不重复题目集合
            # correct_ratio: 所有月份正确率平均值
            if not student_df.empty:
                total_features = {
                    'student_ID': student_id,
                    'submit_count': self.calculate_submit_count(student_df),  # 所有月份总提交次数
                    'active_days': self.calculate_active_days(student_df),  # 所有月份不重复日期数
                    'question_count': self.calculate_question_count(student_df),  # 所有月份不重复题目数
                    'correct_ratio': self.calculate_correct_ratio(student_df),  # 所有月份总体正确率
                    'month_count': student_df['month'].nunique()
                }
                student_features.append(total_features)
        
        return pd.DataFrame(student_features)
    
    def classify_learning_pattern(self, features_df):
        """
        分类学习模式
        
        参数:
            features_df: DataFrame，包含所有学生的特征
        
        返回:
            DataFrame: 添加了pattern列的特征DataFrame
        """
        if features_df.empty:
            return features_df
        
        feature_cols = ['submit_count', 'active_days', 'question_count', 'correct_ratio']
        
        # 如果数据量太少（少于3个学生），直接分类为集中针对型
        if len(features_df) < 3:
            features_df['cluster'] = 0
            features_df['pattern'] = '集中针对型'
            return features_df
        
        # 标准化特征
        scaler = StandardScaler()
        X = scaler.fit_transform(features_df[feature_cols])
        
        # K-Means聚类（k=3），但如果数据量少于3，使用更小的k值
        n_clusters = min(3, len(features_df))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X)
        features_df['cluster'] = clusters
        
        # 计算簇特征均值
        cluster_means = features_df.groupby('cluster')[feature_cols].mean()
        
        # 计算全局中位数（避免除零）
        global_medians = features_df[feature_cols].median()
        global_medians = global_medians.replace(0, 1)  # 避免除零
        
        # 计算相对比例
        cluster_ratios = cluster_means / global_medians
        
        # 为每个学生分类模式
        patterns = []
        for idx, row in features_df.iterrows():
            cluster = row['cluster']
            ratios = cluster_ratios.loc[cluster]
            
            submit_ratio = ratios['submit_count']
            active_ratio = ratios['active_days']
            question_ratio = ratios['question_count']
            correct_ratio = ratios['correct_ratio']
            
            # 模式分类规则（按文档4.2.4）
            if submit_ratio >= 0.85 and correct_ratio >= 0.85:
                pattern = '探索尝试型'
            elif question_ratio >= 0.85 and correct_ratio < 0.85 and active_ratio >= 0.8:
                pattern = '广泛多样型'
            else:
                pattern = '集中针对型'
            
            patterns.append(pattern)
        
        features_df['pattern'] = patterns
        return features_df
    
    def get_pattern_distribution(self, class_name=None, month=None):
        """
        获取学习模式分布
        
        参数:
            class_name: 班级名称
            month: 月份（可选）
        
        返回:
            dict: 模式分布统计
        """
        # 获取所有学生特征
        features_df = self.get_all_students_features(class_name, month)
        
        if features_df.empty:
            return {
                'patterns': {},
                'total': 0,
                'distribution': []
            }
        
        # 分类模式
        features_df = self.classify_learning_pattern(features_df)
        
        # 统计分布
        pattern_counts = features_df['pattern'].value_counts().to_dict()
        total = len(features_df)
        
        distribution = [
            {
                'pattern': pattern,
                'count': count,
                'percentage': round(count / total * 100, 2) if total > 0 else 0
            }
            for pattern, count in pattern_counts.items()
        ]
        
        return {
            'patterns': pattern_counts,
            'total': total,
            'distribution': distribution
        }
    
    def get_student_pattern(self, student_id, class_name=None, month=None):
        """
        获取单个学生的学习模式
        
        参数:
            student_id: 学生ID
            class_name: 班级名称（可选）
            month: 月份（可选）
        
        返回:
            str: 学习模式
        """
        # 获取所有学生特征并分类
        features_df = self.get_all_students_features(class_name, month)
        
        if features_df.empty:
            return '集中针对型'
        
        features_df = self.classify_learning_pattern(features_df)
        
        # 查找该学生的模式
        student_row = features_df[features_df['student_ID'] == student_id]
        if not student_row.empty:
            return student_row.iloc[0]['pattern']
        
        return '集中针对型'
    
    def get_available_months(self, student_id=None, class_name=None):
        """
        获取可用月份列表
        
        参数:
            student_id: 学生ID（可选）
            class_name: 班级名称（可选）
        
        返回:
            list: 月份列表（格式：YYYY-MM）
        """
        # 加载数据
        if class_name:
            df = self._load_submit_records(class_name)
        else:
            df = self._load_submit_records()
        
        # 筛选数据
        df = self._filter_data(df, student_id, class_name)
        
        if df.empty:
            return []
        
        # 获取唯一月份并排序
        months = sorted(df['month'].unique().tolist())
        return months
    
    def get_comparison_data(self, student_id=None, class_name=None, month=None):
        """
        获取对比数据（用于雷达图）
        
        参数:
            student_id: 学生ID（可选）
            class_name: 班级名称（可选）
            month: 月份（可选）
        
        返回:
            dict: 平均值数据
        """
        # 获取所有学生特征
        features_df = self.get_all_students_features(class_name, month)
        
        if features_df.empty:
            return {
                'submit_count_avg': 0,
                'active_days_avg': 0,
                'question_count_avg': 0,
                'correct_ratio_avg': 0.0
            }
        
        # 计算平均值
        return {
            'submit_count_avg': float(features_df['submit_count'].mean()),
            'active_days_avg': float(features_df['active_days'].mean()),
            'question_count_avg': float(features_df['question_count'].mean()),
            'correct_ratio_avg': float(features_df['correct_ratio'].mean())
        }
    
    def get_pattern_ratio(self, student_id, class_name=None, month=None):
        """
        获取学生的学习模式相对比例
        
        参数:
            student_id: 学生ID
            class_name: 班级名称（可选）
            month: 月份（可选）
        
        返回:
            dict: 包含submit_ratio, active_ratio, question_ratio, correct_ratio
        """
        # 获取所有学生特征
        features_df = self.get_all_students_features(class_name, month)
        
        if features_df.empty:
            return {
                'submit_ratio': 0.0,
                'active_ratio': 0.0,
                'question_ratio': 0.0,
                'correct_ratio': 0.0
            }
        
        # 分类模式（这会计算簇比例）
        features_df = self.classify_learning_pattern(features_df)
        
        # 查找该学生
        student_row = features_df[features_df['student_ID'] == student_id]
        if student_row.empty:
            return {
                'submit_ratio': 0.0,
                'active_ratio': 0.0,
                'question_ratio': 0.0,
                'correct_ratio': 0.0
            }
        
        # 获取该学生所属的簇
        cluster = student_row.iloc[0]['cluster']
        
        # 计算簇特征均值
        feature_cols = ['submit_count', 'active_days', 'question_count', 'correct_ratio']
        cluster_means = features_df.groupby('cluster')[feature_cols].mean()
        
        # 计算全局中位数
        global_medians = features_df[feature_cols].median()
        
        # 计算相对比例
        cluster_ratios = cluster_means / global_medians
        ratios = cluster_ratios.loc[cluster]
        
        return {
            'submit_ratio': float(ratios['submit_count']),
            'active_ratio': float(ratios['active_days']),
            'question_ratio': float(ratios['question_count']),
            'correct_ratio': float(ratios['correct_ratio'])
        }