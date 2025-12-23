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
    
    def get_knowledge_mastery_trend(
        self,
        student_id,
        class_name=None,
        start_month=None,
        end_month=None,
        top_k=4,
        knowledge_ids=None
    ):
        """
        获取知识点掌握度趋势数据（用于绿色框2折线图）

        参数:
            student_id: 学生ID（必填）
            class_name: 班级名称（可选，用于限定班级数据）
            start_month: 起始月份（YYYY-MM，可选）
            end_month: 结束月份（YYYY-MM，可选）
            top_k: 自动选择的关键知识点数量（在未显式指定knowledge_ids时生效）
            knowledge_ids: 需要返回趋势的知识点ID列表（优先级高于top_k）

        返回:
            dict: 包含 student, mastery_trend, meta
        """
        if not student_id:
            return {
                'student': {},
                'mastery_trend': {},
                'meta': {
                    'start_month': start_month,
                    'end_month': end_month,
                    'selected_knowledge_ids': [],
                    'total_available_knowledge': 0
                }
            }

        # 如果未提供class_name，可以用于meta中展示，但不要用于过滤逻辑
        # 过滤逻辑与 get_hour_distribution / get_monthly_heatmap 保持一致：
        # - 有 class_name 时按班级限定
        # - 无 class_name 时加载全部班级，只按 student_id 过滤
        resolved_class_name = class_name
        student_name = None
        try:
            student_info = self._load_student_info()
            row = student_info[student_info['student_ID'] == student_id]
            if not row.empty and resolved_class_name is None:
                resolved_class_name = row.iloc[0]['major']
        except Exception:
            pass

        # 加载提交记录（与其他接口保持一致）
        if class_name:
            df = self._load_submit_records(class_name)
        else:
            df = self._load_submit_records()

        # 先按student_id / class_name筛选，再按月份筛选
        df = self._filter_data(df, student_id, class_name)

        if df.empty:
            return {
                'student': {
                    'id': student_id,
                    'name': student_name,
                    'class_name': resolved_class_name
                },
                'mastery_trend': {},
                'meta': {
                    'start_month': start_month,
                    'end_month': end_month,
                    'selected_knowledge_ids': [],
                    'total_available_knowledge': 0
                }
            }

        # 处理月份范围（逻辑与get_monthly_heatmap保持一致）
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
                    'student': {
                        'id': student_id,
                        'name': student_name,
                        'class_name': resolved_class_name
                    },
                    'mastery_trend': {},
                    'meta': {
                        'start_month': start_month,
                        'end_month': end_month,
                        'selected_knowledge_ids': [],
                        'total_available_knowledge': 0
                    }
                }

        # 筛选月份范围
        df = df[(df['month'] >= start_month) & (df['month'] <= end_month)]
        if df.empty:
            return {
                'student': {
                    'id': student_id,
                    'name': student_name,
                    'class_name': resolved_class_name
                },
                'mastery_trend': {},
                'meta': {
                    'start_month': start_month,
                    'end_month': end_month,
                    'selected_knowledge_ids': [],
                    'total_available_knowledge': 0
                }
            }

        # 合并题目信息以获得knowledge字段
        title_info = self._load_title_info()
        if 'knowledge' not in df.columns:
            df = df.merge(title_info[['title_ID', 'knowledge']], on='title_ID', how='left')

        # 统计每个知识点的整体掌握度（用于选择top_k）
        knowledge_groups = df.groupby('knowledge')
        all_knowledge_ids = sorted(knowledge_groups.groups.keys())

        overall_mastery = []
        for knowledge_id, group_df in knowledge_groups:
            submit_count = len(group_df)
            correct_count = len(group_df[group_df['state'].isin(['Absolutely_Correct', 'Partially_Correct'])])
            mastery = correct_count / submit_count if submit_count > 0 else 0.0
            overall_mastery.append({
                'knowledge_id': knowledge_id,
                'mastery': mastery
            })

        # 确定要返回的知识点列表
        if knowledge_ids:
            selected_ids = [kid for kid in knowledge_ids if kid in all_knowledge_ids]
        else:
            overall_mastery.sort(key=lambda x: x['mastery'])
            selected_ids = [item['knowledge_id'] for item in overall_mastery[:top_k]]

        # 构建趋势数据
        mastery_trend = {}
        for knowledge_id in selected_ids:
            k_df = df[df['knowledge'] == knowledge_id]
            if k_df.empty:
                continue

            month_groups = k_df.groupby('month')
            series = []
            for month, month_df in month_groups:
                submit_count = len(month_df)
                correct_count = len(month_df[month_df['state'].isin(['Absolutely_Correct', 'Partially_Correct'])])
                mastery = correct_count / submit_count if submit_count > 0 else 0.0
                series.append({
                    'month': month,
                    'mastery': round(mastery, 4),
                    'mastery_percentage': round(mastery * 100, 2)
                })

            series.sort(key=lambda x: x['month'])

            mastery_trend[knowledge_id] = {
                'knowledge_id': knowledge_id,
                'knowledge_name': f'知识点{knowledge_id}',
                'series': series
            }

        return {
            'student': {
                'id': student_id,
                'name': student_name,
                'class_name': resolved_class_name
            },
            'mastery_trend': mastery_trend,
            'meta': {
                'start_month': start_month,
                'end_month': end_month,
                'selected_knowledge_ids': list(mastery_trend.keys()),
                'total_available_knowledge': len(all_knowledge_ids)
            }
        }
    
    def get_learning_mode_analysis(self, class_name=None, student_id=None, month=None):
        """
        获取学习模式分析数据（用于绿色框2 - 4个散点图）
        
        参数:
            class_name: 班级名称（可选，如 Class1）
            student_id: 学生ID（可选）
            month: 月份筛选（可选，格式：YYYY-MM）
        
        返回:
            dict: 包含4个散点图的数据
        """
        import numpy as np
        from scipy.stats import pearsonr
        
        # 加载提交记录
        if class_name:
            df = self._load_submit_records(class_name)
        else:
            df = self._load_submit_records()
        
        # 筛选数据
        df = self._filter_data(df, student_id, class_name, month)
        
        if df.empty:
            return {
                'class': class_name,
                'student': student_id,
                'month': month,
                'scatter_plots': {
                    'learning_duration': {'title': '知识掌握程度 vs 学习时长', 'x_axis_label': '学习时长', 'y_axis_label': '知识掌握程度(%)', 'data': [], 'statistics': {}},
                    'coding_habits': {'title': '知识掌握程度 vs 编程习惯', 'x_axis_label': '编程习惯', 'y_axis_label': '知识掌握程度(%)', 'data': [], 'statistics': {}},
                    'average_score': {'title': '知识掌握程度 vs 平均得分', 'x_axis_label': '平均得分', 'y_axis_label': '知识掌握程度(%)', 'data': [], 'statistics': {}},
                    'submit_count': {'title': '知识掌握程度 vs 提交次数', 'x_axis_label': '提交次数', 'y_axis_label': '知识掌握程度(%)', 'data': [], 'statistics': {}}
                }
            }
        
        # 加载知识点掌握度数据
        knowledge_mastery_df = self._load_knowledge_mastery()
        
        # 加载学生信息（用于获取学生名称）
        student_info_df = self._load_student_info()
        
        # 按学生分组计算各项指标
        student_stats = []
        student_groups = df.groupby('student_ID')
        
        for student_id, student_df in student_groups:
            # 1. 学习时长（累加timeconsume，秒转小时）
            if 'timeconsume' in student_df.columns:
                # 确保timeconsume是数值类型
                timeconsume_numeric = pd.to_numeric(student_df['timeconsume'], errors='coerce').fillna(0)
                learning_duration = timeconsume_numeric.sum() / 3600.0
            else:
                # 如果没有timeconsume，用时间跨度估算
                if 'datetime' in student_df.columns:
                    time_span = (student_df['datetime'].max() - student_df['datetime'].min()).total_seconds() / 3600.0
                    learning_duration = max(time_span, 0.1)  # 至少0.1小时
                else:
                    learning_duration = 0.0
            
            # 2. 平均得分（确保score是数值类型）
            if 'score' in student_df.columns:
                score_numeric = pd.to_numeric(student_df['score'], errors='coerce').fillna(0)
                average_score = score_numeric.mean()
            else:
                average_score = 0.0
            
            # 3. 提交次数
            submit_count = len(student_df)
            
            # 4. 编程习惯得分（基于方法使用的一致性、多样性）
            coding_habits_score = self._calculate_coding_habits(student_df)
            
            # 5. 知识掌握程度（从individual_knowledge_mastery获取平均值）
            student_mastery = knowledge_mastery_df[knowledge_mastery_df['student_ID'] == student_id]
            if not student_mastery.empty:
                # 确保knowledge_mastery_score是数值类型
                mastery_scores = pd.to_numeric(student_mastery['knowledge_mastery_score'], errors='coerce').fillna(0)
                mastery_avg = mastery_scores.mean()
                mastery_percentage = min(mastery_avg * 100, 80.0)  # 限制在0-80%
            else:
                mastery_percentage = 0.0
            
            # 获取学生名称
            student_name = None
            if not student_info_df.empty:
                student_row = student_info_df[student_info_df['student_ID'] == student_id]
                if not student_row.empty:
                    student_name = f"学生{student_id[:8]}"  # 简化显示
            
            student_stats.append({
                'student_ID': student_id,
                'student_name': student_name,
                'learning_duration': learning_duration,
                'average_score': average_score,
                'submit_count': submit_count,
                'coding_habits': coding_habits_score,
                'mastery_percentage': mastery_percentage
            })
        
        # 构建4个散点图的数据
        scatter_plots = {}
        
        # 1. learning_duration
        learning_duration_data = [
            {
                'student_ID': s['student_ID'],
                'x_value': round(s['learning_duration'], 2),
                'y_value': round(s['mastery_percentage'], 2),
                'student_name': s['student_name']
            }
            for s in student_stats if s['mastery_percentage'] > 0
        ]
        scatter_plots['learning_duration'] = self._build_scatter_plot(
            '知识掌握程度 vs 学习时长',
            '学习时长',
            '知识掌握程度(%)',
            learning_duration_data,
            'learning_duration'
        )
        
        # 2. coding_habits
        coding_habits_data = [
            {
                'student_ID': s['student_ID'],
                'x_value': round(s['coding_habits'], 4),
                'y_value': round(s['mastery_percentage'], 2),
                'student_name': s['student_name']
            }
            for s in student_stats if s['mastery_percentage'] > 0
        ]
        scatter_plots['coding_habits'] = self._build_scatter_plot(
            '知识掌握程度 vs 编程习惯',
            '编程习惯',
            '知识掌握程度(%)',
            coding_habits_data,
            'coding_habits'
        )
        
        # 3. average_score
        average_score_data = [
            {
                'student_ID': s['student_ID'],
                'x_value': round(s['average_score'], 2),
                'y_value': round(s['mastery_percentage'], 2),
                'student_name': s['student_name']
            }
            for s in student_stats if s['mastery_percentage'] > 0
        ]
        scatter_plots['average_score'] = self._build_scatter_plot(
            '知识掌握程度 vs 平均得分',
            '平均得分',
            '知识掌握程度(%)',
            average_score_data,
            'average_score'
        )
        
        # 4. submit_count
        submit_count_data = [
            {
                'student_ID': s['student_ID'],
                'x_value': s['submit_count'],
                'y_value': round(s['mastery_percentage'], 2),
                'student_name': s['student_name']
            }
            for s in student_stats if s['mastery_percentage'] > 0
        ]
        scatter_plots['submit_count'] = self._build_scatter_plot(
            '知识掌握程度 vs 提交次数',
            '提交次数',
            '知识掌握程度(%)',
            submit_count_data,
            'submit_count'
        )
        
        return {
            'class': class_name,
            'student': student_id,
            'month': month,
            'scatter_plots': scatter_plots
        }
    
    def _calculate_coding_habits(self, student_df):
        """
        计算编程习惯得分（0-1之间）
        基于方法使用的一致性、多样性等指标
        """
        if 'method' not in student_df.columns or student_df.empty:
            return 0.0
        
        # 过滤有效方法
        valid_methods = student_df['method'].dropna()
        if valid_methods.empty:
            return 0.0
        
        # 1. 方法使用的一致性：同一题目使用相同方法的比例
        if 'title_ID' in student_df.columns:
            title_method_groups = student_df.groupby('title_ID')['method']
            consistency_scores = []
            for title_id, methods in title_method_groups:
                if len(methods) > 1:
                    # 计算该题目最常用方法的占比
                    method_counts = methods.value_counts()
                    most_common_ratio = method_counts.iloc[0] / len(methods)
                    consistency_scores.append(most_common_ratio)
            method_consistency = np.mean(consistency_scores) if consistency_scores else 0.5
        else:
            method_consistency = 0.5
        
        # 2. 方法使用的多样性：使用不同方法的数量 / 总题目数
        unique_methods = valid_methods.nunique()
        total_questions = student_df['title_ID'].nunique() if 'title_ID' in student_df.columns else len(student_df)
        method_diversity = min(unique_methods / max(total_questions, 1), 1.0)
        
        # 3. 方法选择的合理性：正确率与方法的关联
        if 'state' in student_df.columns:
            correct_states = ['Absolutely_Correct', 'Partially_Correct']
            correct_df = student_df[student_df['state'].isin(correct_states)]
            if len(correct_df) > 0:
                # 计算每个方法的正确率
                method_correctness = correct_df.groupby('method').size() / student_df.groupby('method').size()
                method_effectiveness = method_correctness.mean() if not method_correctness.empty else 0.5
            else:
                method_effectiveness = 0.5
        else:
            method_effectiveness = 0.5
        
        # 综合得分（根据文档中的公式）
        coding_habits_score = (
            method_consistency * 0.4 +
            method_diversity * 0.3 +
            method_effectiveness * 0.3
        )
        
        return round(coding_habits_score, 4)
    
    def _build_scatter_plot(self, title, x_label, y_label, data, plot_type):
        """
        构建散点图数据，包括统计信息
        """
        if not data:
            return {
                'title': title,
                'x_axis_label': x_label,
                'y_axis_label': y_label,
                'data': [],
                'statistics': {
                    'x_min': 0,
                    'x_max': 0,
                    'y_min': 0,
                    'y_max': 80,
                    'correlation': 0.0,
                    'data_count': 0
                }
            }
        
        x_values = [d['x_value'] for d in data]
        y_values = [d['y_value'] for d in data]
        
        # 计算统计信息
        x_min = min(x_values)
        x_max = max(x_values)
        y_min = min(y_values)
        y_max = min(max(y_values), 80)  # Y轴最大值为80
        
        # 计算相关系数
        try:
            from scipy.stats import pearsonr
            import numpy as np
            correlation, _ = pearsonr(x_values, y_values)
            correlation = round(correlation, 2) if not np.isnan(correlation) else 0.0
        except:
            correlation = 0.0
        
        # 根据plot_type设置合理的x_max范围
        if plot_type == 'coding_habits':
            x_max = min(x_max, 1.0)
        elif plot_type == 'average_score':
            x_max = min(x_max, 4.0)
        
        return {
            'title': title,
            'x_axis_label': x_label,
            'y_axis_label': y_label,
            'data': data,
            'statistics': {
                'x_min': round(x_min, 2),
                'x_max': round(x_max, 2),
                'y_min': round(y_min, 2),
                'y_max': round(y_max, 2),
                'correlation': correlation,
                'data_count': len(data)
            }
        }