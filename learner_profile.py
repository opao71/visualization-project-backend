"""
4.2 个性化学习行为模式 - 学习者画像模块
实现时间、方法、知识、趋势维度特征提取
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from collections import defaultdict
from calendar import monthrange

class LearnerProfileAnalyzer:
    """学习者画像分析器"""
    
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.student_info_file = os.path.join(data_dir, 'Data_StudentInfo.csv')
        self.title_info_file = os.path.join(data_dir, 'Data_TitleInfo.csv')
        self.submit_record_dir = os.path.join(data_dir, 'Data_SubmitRecord')
        self.mastery_dir = os.path.join(data_dir, 'mastery')
        self.individual_knowledge_mastery_file = os.path.join(
            self.mastery_dir, 'individual_knowledge_mastery.csv'
        )
        
        # 缓存数据
        self._student_info = None
        self._title_info = None
        self._submit_records = {}
        self._knowledge_mastery = None
    
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
    
    def _load_knowledge_mastery(self):
        """加载知识点掌握度数据"""
        if self._knowledge_mastery is None:
            if os.path.exists(self.individual_knowledge_mastery_file):
                self._knowledge_mastery = pd.read_csv(self.individual_knowledge_mastery_file)
            else:
                self._knowledge_mastery = pd.DataFrame()
        return self._knowledge_mastery
    
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
                    df['day'] = df['datetime'].dt.day
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
                        df['day'] = df['datetime'].dt.day
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
        
        # 过滤有效记录
        df = df[df['state'].isin(['Absolutely_Correct', 'Partially_Correct', 'Error1', 'Error2'])]
        
        return df
    
    def get_hour_distribution(self, student_id=None, class_name=None, month=None):
        """
        获取24小时答题高峰时段分布
        
        参数:
            student_id: 学生ID（可选）
            class_name: 班级名称（可选）
            month: 月份（可选）
        
        返回:
            dict: 包含hour_distribution, peak_hours, total_count
        """
        # 加载数据
        if class_name:
            df = self._load_submit_records(class_name)
        else:
            df = self._load_submit_records()
        
        # 筛选数据
        df = self._filter_data(df, student_id, class_name, month)
        
        if df.empty:
            # 返回空数据（24小时全为0）
            hour_distribution = [
                {'hour': h, 'count': 0, 'percentage': 0.0}
                for h in range(24)
            ]
            return {
                'hour_distribution': hour_distribution,
                'peak_hours': [],
                'total_count': 0
            }
        
        # 统计每个小时的提交次数
        hour_counts = df['hour'].value_counts().sort_index()
        total_count = len(df)
        
        # 构建24小时分布
        hour_distribution = []
        for h in range(24):
            count = hour_counts.get(h, 0)
            percentage = (count / total_count * 100) if total_count > 0 else 0.0
            hour_distribution.append({
                'hour': h,
                'count': int(count),
                'percentage': round(percentage, 2)
            })
        
        # 找出高峰时段（前5个）
        peak_hours = hour_counts.nlargest(5).index.tolist()
        
        return {
            'hour_distribution': hour_distribution,
            'peak_hours': [int(h) for h in peak_hours],
            'total_count': int(total_count)
        }
    
    def get_method_preference(self, student_id=None, class_name=None, month=None, top_n=5):
        """
        获取编程方法偏好
        
        参数:
            student_id: 学生ID（可选）
            class_name: 班级名称（可选）
            month: 月份（可选）
            top_n: 返回前N种方法，默认5
        
        返回:
            dict: 包含method_distribution, total_methods
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
                'method_distribution': [],
                'total_methods': 0
            }
        
        # 统计方法使用次数
        method_counts = df['method'].value_counts()
        total_submits = len(df)
        
        # 取前top_n个方法
        top_methods = method_counts.head(top_n)
        other_count = method_counts.iloc[top_n:].sum() if len(method_counts) > top_n else 0
        
        method_distribution = []
        
        # 添加前top_n个方法
        for idx, (method, count) in enumerate(top_methods.items(), 1):
            ratio = count / total_submits if total_submits > 0 else 0.0
            # 使用方法字段本身作为方法名称，如果method是代码格式则保持原样
            method_name = str(method) if method else f'方法{idx}'
            method_distribution.append({
                'method': method,
                'method_name': method_name,
                'count': int(count),
                'ratio': round(ratio, 4),
                'percentage': round(ratio * 100, 2)
            })
        
        # 添加"其他"类别
        if other_count > 0:
            other_ratio = other_count / total_submits if total_submits > 0 else 0.0
            method_distribution.append({
                'method': 'Method_other',
                'method_name': '其他',
                'count': int(other_count),
                'ratio': round(other_ratio, 4),
                'percentage': round(other_ratio * 100, 2)
            })
        
        return {
            'method_distribution': method_distribution,
            'total_methods': len(method_distribution)
        }
    
    def get_knowledge_mastery(self, student_id=None, class_name=None, month=None):
        """
        获取知识点掌握情况
        
        参数:
            student_id: 学生ID（可选）
            class_name: 班级名称（可选）
            month: 月份（可选）
        
        返回:
            dict: 包含knowledge_stats, summary
        """
        # 加载题目信息
        title_info = self._load_title_info()
        
        # 加载提交记录
        if class_name:
            df = self._load_submit_records(class_name)
        else:
            df = self._load_submit_records()
        
        # 筛选数据
        df = self._filter_data(df, student_id, class_name, month)
        
        if df.empty:
            return {
                'knowledge_stats': [],
                'summary': {
                    'total_knowledge': 0,
                    'good_count': 0,
                    'medium_count': 0,
                    'poor_count': 0
                }
            }
        
        # 合并题目信息获取知识点
        df = df.merge(title_info[['title_ID', 'knowledge', 'score']], on='title_ID', how='left')
        
        # 如果指定了学生ID，尝试从mastery文件读取
        if student_id:
            mastery_df = self._load_knowledge_mastery()
            if not mastery_df.empty:
                student_mastery = mastery_df[mastery_df['student_ID'] == student_id]
                if not student_mastery.empty:
                    # 从mastery文件读取
                    knowledge_stats = []
                    for _, row in student_mastery.iterrows():
                        knowledge_id = row['knowledge']
                        # mastery_score已经是0-1之间的值，不需要除以total_score
                        mastery = float(row['knowledge_mastery_score']) if 'knowledge_mastery_score' in row else 0.0
                        
                        # 计算该知识点的统计信息
                        knowledge_df = df[df['knowledge'] == knowledge_id]
                        question_count = knowledge_df['title_ID'].nunique()
                        submit_count = len(knowledge_df)
                        correct_count = len(knowledge_df[knowledge_df['state'].isin(['Absolutely_Correct', 'Partially_Correct'])])
                        
                        # 判断掌握度等级
                        if mastery >= 0.6:
                            level = 'good'
                        elif mastery >= 0.4:
                            level = 'medium'
                        else:
                            level = 'poor'
                        
                        knowledge_stats.append({
                            'knowledge_id': knowledge_id,
                            'knowledge_name': f'知识点{knowledge_id}',
                            'mastery': round(mastery, 4),
                            'mastery_percentage': round(mastery * 100, 2),
                            'question_count': int(question_count),
                            'submit_count': int(submit_count),
                            'correct_count': int(correct_count),
                            'level': level
                        })
                    
                    # 统计汇总
                    good_count = sum(1 for k in knowledge_stats if k['level'] == 'good')
                    medium_count = sum(1 for k in knowledge_stats if k['level'] == 'medium')
                    poor_count = sum(1 for k in knowledge_stats if k['level'] == 'poor')
                    
                    return {
                        'knowledge_stats': knowledge_stats,
                        'summary': {
                            'total_knowledge': len(knowledge_stats),
                            'good_count': good_count,
                            'medium_count': medium_count,
                            'poor_count': poor_count
                        }
                    }
        
        # 如果没有mastery文件或群体分析，从提交记录计算
        knowledge_stats = []
        knowledge_groups = df.groupby('knowledge')
        
        for knowledge_id, group_df in knowledge_groups:
            # 计算该知识点的题目数
            question_count = group_df['title_ID'].nunique()
            
            # 计算提交次数和正确次数
            submit_count = len(group_df)
            correct_count = len(group_df[group_df['state'].isin(['Absolutely_Correct', 'Partially_Correct'])])
            
            # 计算掌握度（正确率）
            mastery = correct_count / submit_count if submit_count > 0 else 0.0
            
            # 判断掌握度等级
            if mastery >= 0.6:
                level = 'good'
            elif mastery >= 0.4:
                level = 'medium'
            else:
                level = 'poor'
            
            knowledge_stats.append({
                'knowledge_id': knowledge_id,
                'knowledge_name': f'知识点{knowledge_id}',
                'mastery': round(mastery, 4),
                'mastery_percentage': round(mastery * 100, 2),
                'question_count': int(question_count),
                'submit_count': int(submit_count),
                'correct_count': int(correct_count),
                'level': level
            })
        
        # 统计汇总
        good_count = sum(1 for k in knowledge_stats if k['level'] == 'good')
        medium_count = sum(1 for k in knowledge_stats if k['level'] == 'medium')
        poor_count = sum(1 for k in knowledge_stats if k['level'] == 'poor')
        
        return {
            'knowledge_stats': knowledge_stats,
            'summary': {
                'total_knowledge': len(knowledge_stats),
                'good_count': good_count,
                'medium_count': medium_count,
                'poor_count': poor_count
            }
        }
    
    def get_monthly_stats(self, student_id=None, class_name=None):
        """
        获取月度学习趋势
        
        参数:
            student_id: 学生ID（可选）
            class_name: 班级名称（可选）
        
        返回:
            list: 月度统计数据列表
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
        
        # 按月分组统计
        monthly_stats = []
        month_groups = df.groupby('month')
        
        for month, month_df in month_groups:
            submit_count = len(month_df)
            question_count = month_df['title_ID'].nunique()
            correct_count = len(month_df[month_df['state'].isin(['Absolutely_Correct', 'Partially_Correct'])])
            correct_ratio = correct_count / submit_count if submit_count > 0 else 0.0
            
            monthly_stats.append({
                'month': month,
                'submit_count': int(submit_count),
                'question_count': int(question_count),
                'correct_count': int(correct_count),
                'correct_ratio': round(correct_ratio, 4),
                'correct_percentage': round(correct_ratio * 100, 2)
            })
        
        # 按月份排序
        monthly_stats.sort(key=lambda x: x['month'])
        
        return monthly_stats
    
    def get_monthly_heatmap(self, student_id=None, class_name=None, start_month=None, end_month=None):
        """
        获取月度活动热力图数据
        
        参数:
            student_id: 学生ID（可选）
            class_name: 班级名称（可选）
            start_month: 起始月份（格式：YYYY-MM）
            end_month: 结束月份（格式：YYYY-MM）
        
        返回:
            dict: 包含heatmap_data, summary
        """
        # 加载数据
        if class_name:
            df = self._load_submit_records(class_name)
        else:
            df = self._load_submit_records()
        
        # 筛选数据
        df = self._filter_data(df, student_id, class_name)
        
        if df.empty:
            return {
                'heatmap_data': [],
                'summary': {
                    'total_days': 0,
                    'active_days': 0,
                    'max_count': 0,
                    'min_count': 0
                }
            }
        
        # 如果没有指定月份范围，默认使用最近3个月
        if not start_month or not end_month:
            months = sorted(df['month'].unique())
            if len(months) >= 3:
                start_month = months[-3]
                end_month = months[-1]
            elif len(months) > 0:
                start_month = months[0]
                end_month = months[-1]
            else:
                return {
                    'heatmap_data': [],
                    'summary': {
                        'total_days': 0,
                        'active_days': 0,
                        'max_count': 0,
                        'min_count': 0
                    }
                }
        
        # 筛选月份范围
        df = df[(df['month'] >= start_month) & (df['month'] <= end_month)]
        
        if df.empty:
            return {
                'heatmap_data': [],
                'summary': {
                    'total_days': 0,
                    'active_days': 0,
                    'max_count': 0,
                    'min_count': 0
                }
            }
        
        # 按月份和日期分组统计
        df['year_month'] = df['datetime'].dt.to_period('M').astype(str)
        df['day'] = df['datetime'].dt.day
        
        heatmap_data = []
        all_days = []
        
        # 获取所有月份
        months = sorted(df['year_month'].unique())
        
        for month in months:
            month_df = df[df['year_month'] == month]
            
            # 获取该月的天数
            year, month_num = map(int, month.split('-'))
            days_in_month = monthrange(year, month_num)[1]
            
            # 按日期统计提交次数
            day_counts = month_df.groupby('day').size()
            
            days = []
            for day in range(1, days_in_month + 1):
                count = int(day_counts.get(day, 0))
                all_days.append(count)
                
                # 判断活动等级
                if count == 0:
                    level = 'none'
                elif count <= 5:
                    level = 'low'
                elif count <= 15:
                    level = 'medium'
                else:
                    level = 'high'
                
                days.append({
                    'day': day,
                    'count': count,
                    'level': level
                })
            
            # 月份名称（中文）
            month_name = f'{month_num}月'
            
            heatmap_data.append({
                'month': month,
                'month_name': month_name,
                'days': days
            })
        
        # 计算汇总统计
        total_days = sum(len(month_data['days']) for month_data in heatmap_data)
        active_days = sum(1 for count in all_days if count > 0)
        max_count = max(all_days) if all_days else 0
        min_count = min(all_days) if all_days else 0
        
        return {
            'heatmap_data': heatmap_data,
            'summary': {
                'total_days': total_days,
                'active_days': active_days,
                'max_count': max_count,
                'min_count': min_count
            }
        }