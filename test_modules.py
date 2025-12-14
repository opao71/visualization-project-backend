"""
4.2 个性化学习行为模式 - 数据处理脚本
处理所有数据并将结果输出到CSV文件
"""
import os
import sys
import pandas as pd
from learning_behavior import LearningBehaviorAnalyzer
from learner_profile import LearnerProfileAnalyzer

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'data', 'learning_behavior')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_learning_behavior():
    """处理学习行为分析数据并输出CSV"""
    print("=" * 60)
    print("处理学习行为分析数据")
    print("=" * 60)
    
    analyzer = LearningBehaviorAnalyzer(DATA_DIR)
    
    # 1. 处理所有学生的学习行为特征和模式分类
    print("\n1. 处理所有学生的学习行为特征和模式分类...")
    all_students_features = analyzer.get_all_students_features()
    
    if not all_students_features.empty:
        # 分类学习模式
        all_students_features = analyzer.classify_learning_pattern(all_students_features)
        
        # 添加模式比例信息
        feature_cols = ['submit_count', 'active_days', 'question_count', 'correct_ratio']
        cluster_means = all_students_features.groupby('cluster')[feature_cols].mean()
        global_medians = all_students_features[feature_cols].median()
        global_medians = global_medians.replace(0, 1)
        cluster_ratios = cluster_means / global_medians
        
        # 为每个学生添加比例信息
        ratios_list = []
        for idx, row in all_students_features.iterrows():
            cluster = row['cluster']
            ratios = cluster_ratios.loc[cluster]
            ratios_list.append({
                'student_ID': row['student_ID'],
                'submit_ratio': float(ratios['submit_count']),
                'active_ratio': float(ratios['active_days']),
                'question_ratio': float(ratios['question_count']),
                'correct_ratio': float(ratios['correct_ratio'])
            })
        
        ratios_df = pd.DataFrame(ratios_list)
        all_students_features = all_students_features.merge(ratios_df, on='student_ID', how='left')
        
        # 保存到CSV
        output_file = os.path.join(OUTPUT_DIR, 'student_behavior_features.csv')
        all_students_features.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   ✓ 已保存: {output_file} ({len(all_students_features)}条记录)")
    
    # 2. 处理各班级的模式分布
    print("\n2. 处理各班级的学习模式分布...")
    student_info = pd.read_csv(os.path.join(DATA_DIR, 'Data_StudentInfo.csv'))
    classes = sorted(student_info['major'].unique().tolist())
    
    class_pattern_distributions = []
    for class_name in classes:
        distribution = analyzer.get_pattern_distribution(class_name=class_name)
        if distribution['total'] > 0:
            for item in distribution['distribution']:
                class_pattern_distributions.append({
                    'class_name': class_name,
                    'pattern': item['pattern'],
                    'count': item['count'],
                    'percentage': item['percentage'],
                    'total': distribution['total']
                })
    
    if class_pattern_distributions:
        pattern_dist_df = pd.DataFrame(class_pattern_distributions)
        output_file = os.path.join(OUTPUT_DIR, 'class_pattern_distribution.csv')
        pattern_dist_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   ✓ 已保存: {output_file} ({len(pattern_dist_df)}条记录)")
    
    # 3. 处理按月统计的学习行为特征
    print("\n3. 处理按月统计的学习行为特征...")
    all_months = analyzer.get_available_months()
    monthly_features = []
    
    for month in all_months:
        features_df = analyzer.get_all_students_features(month=month)
        if not features_df.empty:
            features_df = analyzer.classify_learning_pattern(features_df)
            features_df['month'] = month
            monthly_features.append(features_df)
    
    if monthly_features:
        monthly_df = pd.concat(monthly_features, ignore_index=True)
        output_file = os.path.join(OUTPUT_DIR, 'monthly_behavior_features.csv')
        monthly_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   ✓ 已保存: {output_file} ({len(monthly_df)}条记录)")
    
    print("\n✓ 学习行为分析数据处理完成")

def process_learner_profile():
    """处理学习者画像数据并输出CSV"""
    print("\n" + "=" * 60)
    print("处理学习者画像数据")
    print("=" * 60)
    
    analyzer = LearnerProfileAnalyzer(DATA_DIR)
    behavior_analyzer = LearningBehaviorAnalyzer(DATA_DIR)
    
    # 获取所有学生ID
    student_info = pd.read_csv(os.path.join(DATA_DIR, 'Data_StudentInfo.csv'))
    all_students = student_info['student_ID'].unique()
    
    # 1. 处理所有学生的24小时分布
    print("\n1. 处理所有学生的24小时答题分布...")
    hour_distributions = []
    for student_id in all_students:
        hour_dist = analyzer.get_hour_distribution(student_id=student_id)
        if hour_dist['total_count'] > 0:
            for hour_data in hour_dist['hour_distribution']:
                hour_distributions.append({
                    'student_ID': student_id,
                    'hour': hour_data['hour'],
                    'count': hour_data['count'],
                    'percentage': hour_data['percentage']
                })
    
    if hour_distributions:
        hour_df = pd.DataFrame(hour_distributions)
        output_file = os.path.join(OUTPUT_DIR, 'student_hour_distribution.csv')
        hour_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   ✓ 已保存: {output_file} ({len(hour_df)}条记录)")
    
    # 2. 处理所有学生的编程方法偏好
    print("\n2. 处理所有学生的编程方法偏好...")
    method_preferences = []
    for student_id in all_students:
        method_pref = analyzer.get_method_preference(student_id=student_id, top_n=10)
        if method_pref['total_methods'] > 0:
            for method in method_pref['method_distribution']:
                method_preferences.append({
                    'student_ID': student_id,
                    'method': method['method'],
                    'method_name': method['method_name'],
                    'count': method['count'],
                    'ratio': method['ratio'],
                    'percentage': method['percentage']
                })
    
    if method_preferences:
        method_df = pd.DataFrame(method_preferences)
        output_file = os.path.join(OUTPUT_DIR, 'student_method_preference.csv')
        method_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   ✓ 已保存: {output_file} ({len(method_df)}条记录)")
    
    # 3. 处理所有学生的知识点掌握情况
    print("\n3. 处理所有学生的知识点掌握情况...")
    knowledge_stats_list = []
    for student_id in all_students:
        knowledge = analyzer.get_knowledge_mastery(student_id=student_id)
        if knowledge['knowledge_stats']:
            for k in knowledge['knowledge_stats']:
                knowledge_stats_list.append({
                    'student_ID': student_id,
                    'knowledge_id': k['knowledge_id'],
                    'knowledge_name': k['knowledge_name'],
                    'mastery': k['mastery'],
                    'mastery_percentage': k['mastery_percentage'],
                    'question_count': k['question_count'],
                    'submit_count': k['submit_count'],
                    'correct_count': k['correct_count'],
                    'level': k['level']
                })
    
    if knowledge_stats_list:
        knowledge_df = pd.DataFrame(knowledge_stats_list)
        output_file = os.path.join(OUTPUT_DIR, 'student_knowledge_mastery.csv')
        knowledge_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   ✓ 已保存: {output_file} ({len(knowledge_df)}条记录)")
    
    # 4. 处理所有学生的月度学习趋势
    print("\n4. 处理所有学生的月度学习趋势...")
    monthly_stats_list = []
    for student_id in all_students:
        monthly = analyzer.get_monthly_stats(student_id=student_id)
        if monthly:
            for m in monthly:
                monthly_stats_list.append({
                    'student_ID': student_id,
                    'month': m['month'],
                    'submit_count': m['submit_count'],
                    'question_count': m['question_count'],
                    'correct_count': m['correct_count'],
                    'correct_ratio': m['correct_ratio'],
                    'correct_percentage': m['correct_percentage']
                })
    
    if monthly_stats_list:
        monthly_stats_df = pd.DataFrame(monthly_stats_list)
        output_file = os.path.join(OUTPUT_DIR, 'student_monthly_stats.csv')
        monthly_stats_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   ✓ 已保存: {output_file} ({len(monthly_stats_df)}条记录)")
    
    # 5. 处理各班级的24小时分布（聚合数据）
    print("\n5. 处理各班级的24小时分布...")
    classes = sorted(student_info['major'].unique().tolist())
    class_hour_distributions = []
    for class_name in classes:
        hour_dist = analyzer.get_hour_distribution(class_name=class_name)
        if hour_dist['total_count'] > 0:
            for hour_data in hour_dist['hour_distribution']:
                class_hour_distributions.append({
                    'class_name': class_name,
                    'hour': hour_data['hour'],
                    'count': hour_data['count'],
                    'percentage': hour_data['percentage']
                })
    
    if class_hour_distributions:
        class_hour_df = pd.DataFrame(class_hour_distributions)
        output_file = os.path.join(OUTPUT_DIR, 'class_hour_distribution.csv')
        class_hour_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   ✓ 已保存: {output_file} ({len(class_hour_df)}条记录)")
    
    # 6. 处理各班级的编程方法偏好（聚合数据）
    print("\n6. 处理各班级的编程方法偏好...")
    class_method_preferences = []
    for class_name in classes:
        method_pref = analyzer.get_method_preference(class_name=class_name, top_n=10)
        if method_pref['total_methods'] > 0:
            for method in method_pref['method_distribution']:
                class_method_preferences.append({
                    'class_name': class_name,
                    'method': method['method'],
                    'method_name': method['method_name'],
                    'count': method['count'],
                    'ratio': method['ratio'],
                    'percentage': method['percentage']
                })
    
    if class_method_preferences:
        class_method_df = pd.DataFrame(class_method_preferences)
        output_file = os.path.join(OUTPUT_DIR, 'class_method_preference.csv')
        class_method_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   ✓ 已保存: {output_file} ({len(class_method_df)}条记录)")
    
    print("\n✓ 学习者画像数据处理完成")

def main():
    """主处理函数"""
    print("\n" + "=" * 60)
    print("开始处理4.2个性化学习行为模式数据")
    print("=" * 60)
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)
    
    try:
        # 处理学习行为分析数据
        process_learning_behavior()
        
        # 处理学习者画像数据
        process_learner_profile()
        
        print("\n" + "=" * 60)
        print("所有数据处理完成！")
        print("=" * 60)
        print(f"处理结果已保存到: {OUTPUT_DIR}")
        print("\n生成的CSV文件列表:")
        if os.path.exists(OUTPUT_DIR):
            csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.csv')]
            for i, f in enumerate(csv_files, 1):
                file_path = os.path.join(OUTPUT_DIR, f)
                file_size = os.path.getsize(file_path) / 1024  # KB
                print(f"  {i}. {f} ({file_size:.2f} KB)")
        
    except Exception as e:
        print(f"\n❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

