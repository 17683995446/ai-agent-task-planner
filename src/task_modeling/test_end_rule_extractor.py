"""
终止规则解析器测试
基于第一性原理的AI Agent任务规划系统
"""
from end_rule_extractor import EndRuleExtractor, extract_end_rule, EndRuleExtractionError


def test_end_rule_extractor():
    """测试终止规则提取器"""
    print("=" * 60)
    print("终止规则解析器测试")
    print("=" * 60)
    
    extractor = EndRuleExtractor()
    
    # 测试用例1：基本需求描述
    print("\n[测试用例1] 基本需求描述")
    desc1 = "生成2024年度销售报告"
    try:
        end_rule1 = extractor.extract(desc1)
        print("✓ 提取成功")
        print(f"成功条件数量: {len(end_rule1.success_conditions)}")
        for sc in end_rule1.success_conditions:
            print(f"  - {sc.id}: {sc.description}")
            print(f"    检查规则: {sc.check_rule}")
        print(f"失败条件数量: {len(end_rule1.failure_conditions)}")
        for fc in end_rule1.failure_conditions:
            print(f"  - {fc.id} (优先级{fc.priority}): {fc.description}")
            print(f"    检查规则: {fc.check_rule}")
        print(f"评估逻辑: {end_rule1.evaluation_logic}")
    except Exception as e:
        print(f"✗ 提取失败: {e}")
    
    # 测试用例2：包含时间限制的描述
    print("\n[测试用例2] 包含时间限制的描述")
    desc2 = "2小时内完成数据分析，超过5次迭代就停止"
    try:
        end_rule2 = extractor.extract(desc2)
        print("✓ 提取成功")
        print(f"成功条件数量: {len(end_rule2.success_conditions)}")
        print(f"失败条件数量: {len(end_rule2.failure_conditions)}")
        for fc in end_rule2.failure_conditions:
            print(f"  - {fc.id}: {fc.description}")
    except Exception as e:
        print(f"✗ 提取失败: {e}")
    
    # 测试用例3：测试便捷函数
    print("\n[测试用例3] 测试便捷函数")
    desc3 = "创建用户登录系统，必须在30分钟内完成"
    try:
        end_rule3 = extract_end_rule(desc3)
        print("✓ 便捷函数调用成功")
        print(f"成功条件数量: {len(end_rule3.success_conditions)}")
        print(f"失败条件数量: {len(end_rule3.failure_conditions)}")
        print("验证is_valid:", end_rule3.is_valid())
    except Exception as e:
        print(f"✗ 便捷函数调用失败: {e}")
    
    # 测试用例4：空输入异常处理
    print("\n[测试用例4] 空输入异常处理")
    try:
        extractor.extract("")
        print("✗ 应该抛出异常但没有")
    except EndRuleExtractionError as e:
        print(f"✓ 正确抛出异常: {e}")
    
    # 测试用例5：复杂需求描述
    print("\n[测试用例5] 复杂需求描述")
    desc5 = "开发一个电商网站，包含用户注册、商品浏览、购物车功能，必须在3天内完成，不能有严重错误，最多迭代20次"
    try:
        end_rule5 = extractor.extract(desc5)
        print("✓ 提取成功")
        print(f"成功条件: {[sc.description for sc in end_rule5.success_conditions]}")
        print(f"失败条件: {[fc.description for fc in end_rule5.failure_conditions]}")
    except Exception as e:
        print(f"✗ 提取失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_end_rule_extractor()
