"""
测试4.2个性化学习行为模式API接口
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_api(endpoint, params=None):
    """测试API接口"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"测试接口: {endpoint}")
    print(f"参数: {params}")
    print(f"{'='*60}")
    
    try:
        # 增加超时时间，因为现在优先从CSV读取，应该更快
        response = requests.get(url, params=params, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # 显示完整响应数据（格式化JSON）
            print("完整响应数据:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return True
        else:
            print(f"错误: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器，请确保Flask应用正在运行")
        return False
    except requests.exceptions.Timeout:
        print("错误: 请求超时（可能数据量较大）")
        return False
    except Exception as e:
        print(f"错误: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("开始测试4.2个性化学习行为模式API接口")
    print("请确保Flask应用正在运行 (python app.py)")
    
    # 测试用例
    test_cases = [
        # 1. 获取可用月份列表
        ("/api/learning-profile/available-months", {"class_name": "J23517"}),
        ("/api/learning-profile/available-months", {"student_id": "8b6d1125760bd3939b6e"}),
        
        # 2. 获取学习行为特征
        ("/api/learning-profile/behavior-features", {"student_id": "8b6d1125760bd3939b6e"}),
        ("/api/learning-profile/behavior-features", {"class_name": "J23517"}),
        ("/api/learning-profile/behavior-features", {"student_id": "8b6d1125760bd3939b6e", "month": "2024-01"}),
        
        # 3. 获取学习模式分布
        ("/api/learning-profile/pattern-distribution", {"class_name": "J23517"}),
        ("/api/learning-profile/pattern-distribution", {"class_name": "J23517", "month": "2024-01"}),
        
        # 4. 获取编程方法偏好
        ("/api/learning-profile/method-preference", {"student_id": "8b6d1125760bd3939b6e"}),
        ("/api/learning-profile/method-preference", {"class_name": "J23517"}),
        
        # 5. 获取知识点掌握情况
        ("/api/learning-profile/knowledge-mastery", {"student_id": "8b6d1125760bd3939b6e"}),
        ("/api/learning-profile/knowledge-mastery", {"class_name": "J23517"}),
        
        # 6. 获取24小时答题高峰时段
        ("/api/learning-profile/hour-distribution", {"student_id": "8b6d1125760bd3939b6e"}),
        ("/api/learning-profile/hour-distribution", {"class_name": "J23517"}),
        
        # 7. 获取月度活动热力图
        ("/api/learning-profile/monthly-heatmap", {"student_id": "8b6d1125760bd3939b6e"}),
        ("/api/learning-profile/monthly-heatmap", {"class_name": "J23517"}),
        
        # 8. 获取蓝色框1综合数据
        ("/api/learning-profile/comprehensive-bluebox1", {"student_id": "8b6d1125760bd3939b6e"}),
        ("/api/learning-profile/comprehensive-bluebox1", {"class_name": "J23517"}),
        
        # 9. 获取蓝色框2综合数据
        ("/api/learning-profile/comprehensive-bluebox2", {"student_id": "8b6d1125760bd3939b6e"}),
        ("/api/learning-profile/comprehensive-bluebox2", {"class_name": "J23517"}),
    ]
    
    results = []
    for endpoint, params in test_cases:
        success = test_api(endpoint, params)
        results.append((endpoint, params, success))
    
    # 统计结果
    print(f"\n{'='*60}")
    print("测试结果统计")
    print(f"{'='*60}")
    success_count = sum(1 for _, _, success in results if success)
    total_count = len(results)
    print(f"成功: {success_count}/{total_count}")
    print(f"失败: {total_count - success_count}/{total_count}")
    
    print("\n失败的测试用例:")
    for endpoint, params, success in results:
        if not success:
            print(f"  - {endpoint} {params}")

if __name__ == "__main__":
    main()

