"""
边界约束提取模块测试
基于第一性原理的AI Agent任务规划系统
"""

from boundary_extractor import BoundaryExtractor, extract_boundary, BoundaryExtractionError


def test_boundary_extractor():
    """测试边界约束提取器"""
    print("=" * 60)
    print("边界约束提取模块测试")
    print("=" * 60)
    
    extractor = BoundaryExtractor()
    
    # 测试用例1：包含范围和时间约束的完整描述
    print("\n[测试用例1] 包含范围和时间约束的完整描述")
    desc1 = "生成2024年度销售报告，包含中国区数据，不包含海外业务，需要在2小时内完成，预算最多1000元，最多尝试5次"
    try:
        boundary1 = extractor.extract(desc1)
        print("✓ 提取成功")
        print(f"  范围包含: {boundary1.scope.inclusions}")
        print(f"  范围排除: {boundary1.scope.exclusions}")
        print(f"  最大时间: {boundary1.resources.max_time_seconds}秒")
        print(f"  最大成本: {boundary1.resources.max_cost}")
        print(f"  最大迭代: {boundary1.resources.max_iterations}次")
        print(f"  质量约束: {boundary1.quality}")
    except Exception as e:
        print(f"✗ 提取失败: {e}")
    
    # 测试用例2：包含质量约束的描述
    print("\n[测试用例2] 包含质量约束的描述")
    desc2 = "创建数据分析模型，要求准确率至少95%，错误率不超过1%"
    try:
        boundary2 = extractor.extract(desc2)
        print("✓ 提取成功")
        print(f"  范围包含: {boundary2.scope.inclusions}")
        print(f"  范围排除: {boundary2.scope.exclusions}")
        print(f"  最大时间: {boundary2.resources.max_time_seconds}秒")
        print(f"  质量约束:")
        if boundary2.quality:
            print(f"    最低准确率: {boundary2.quality.min_accuracy}")
            print(f"    最高错误率: {boundary2.quality.max_error_rate}")
    except Exception as e:
        print(f"✗ 提取失败: {e}")
    
    # 测试用例3：只有基本描述，使用默认值
    print("\n[测试用例3] 只有基本描述，使用默认值")
    desc3 = "写一篇关于AI的文章"
    try:
        boundary3 = extractor.extract(desc3)
        print("✓ 提取成功")
        print(f"  范围包含: {boundary3.scope.inclusions}")
        print(f"  范围排除: {boundary3.scope.exclusions}")
        print(f"  最大时间: {boundary3.resources.max_time_seconds}秒")
        print(f"  最大迭代: {boundary3.resources.max_iterations}次")
        print(f"  质量约束: {boundary3.quality}")
    except Exception as e:
        print(f"✗ 提取失败: {e}")
    
    # 测试用例4：测试便捷函数
    print("\n[测试用例4] 测试便捷函数")
    desc4 = "开发一个网站，预算5000元，30天完成，最多迭代20次，准确率至少90%"
    try:
        boundary4 = extract_boundary(desc4)
        print("✓ 便捷函数调用成功")
        print(f"  最大时间: {boundary4.resources.max_time_seconds}秒")
        print(f"  最大成本: {boundary4.resources.max_cost}")
        print(f"  最大迭代: {boundary4.resources.max_iterations}次")
        if boundary4.quality:
            print(f"  最低准确率: {boundary4.quality.min_accuracy}")
    except Exception as e:
        print(f"✗ 便捷函数调用失败: {e}")
    
    # 测试用例5：空输入异常处理
    print("\n[测试用例5] 空输入异常处理")
    try:
        extractor.extract("")
        print("✗ 应该抛出异常但没有")
    except BoundaryExtractionError as e:
        print(f"✓ 正确抛出异常: {e}")
    
    # 测试用例6：包含各种单位的时间描述
    print("\n[测试用例6] 包含各种单位的时间描述")
    descs = [
        "任务需要在30分钟内完成",
        "预计5小时完成",
        "最多3天完成",
        "120秒内必须完成"
    ]
    for desc in descs:
        try:
            boundary = extractor.extract(desc)
            print(f"  描述: {desc}")
            print(f"  → 提取时间: {boundary.resources.max_time_seconds}秒")
        except Exception as e:
            print(f"  → 提取失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_boundary_extractor()
