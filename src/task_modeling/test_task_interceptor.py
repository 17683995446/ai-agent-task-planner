"""
任务拦截器测试
基于第一性原理的AI Agent任务规划系统
"""

from task_interceptor import (
    TaskInterceptor, intercept_task, TaskRejectionLevel, TaskRejectionReason
)


def test_task_interceptor():
    """测试任务拦截器"""
    print("=" * 60)
    print("任务拦截器测试")
    print("=" * 60)
    
    interceptor = TaskInterceptor()
    
    # 测试用例1：无错误情况
    print("\n[测试用例1] 无错误情况")
    errors1 = []
    response1 = interceptor.intercept(errors1)
    print(f"拒绝级别: {response1.level.value}")
    print(f"是否允许: {response1.is_allowed}")
    print(f"用户消息:\n{response1.to_user_message()}")
    
    # 测试用例2：缺少关键字段（Target缺失）
    print("\n" + "=" * 60)
    print("\n[测试用例2] 缺少关键字段")
    errors2 = ["Target的ID不能为空", "Target的描述不能为空"]
    response2 = interceptor.intercept(errors2)
    print(f"拒绝级别: {response2.level.value}")
    print(f"是否允许: {response2.is_allowed}")
    print(f"错误数量: {len(response2.errors)}")
    print(f"建议数量: {len(response2.suggestions)}")
    print(f"摘要: {response2.summary}")
    print(f"\n用户消息:\n{response2.to_user_message()}")
    
    # 测试用例3：格式错误
    print("\n" + "=" * 60)
    print("\n[测试用例3] 格式错误")
    errors3 = ["Target的优先级必须在1-10之间"]
    response3 = interceptor.intercept(errors3)
    print(f"拒绝级别: {response3.level.value}")
    print(f"是否允许: {response3.is_allowed}")
    print(f"错误详情: {[e.to_dict() for e in response3.errors]}")
    print(f"\n用户消息:\n{response3.to_user_message()}")
    
    # 测试用例4：资源超出
    print("\n" + "=" * 60)
    print("\n[测试用例4] 资源超出（警告级别）")
    errors4 = ["max_time_seconds必须大于0"]
    response4 = interceptor.intercept(errors4)
    print(f"拒绝级别: {response4.level.value}")
    print(f"是否允许: {response4.is_allowed}")
    print(f"\n用户消息:\n{response4.to_user_message()}")
    
    # 测试用例5：多种错误混合
    print("\n" + "=" * 60)
    print("\n[测试用例5] 多种错误混合")
    errors5 = [
        "Target的ID不能为空",
        "Condition至少需要一个条件",
        "max_cost不能为负数",
        "EndRule至少需要一个成功条件"
    ]
    response5 = interceptor.intercept(errors5)
    print(f"拒绝级别: {response5.level.value}")
    print(f"是否允许: {response5.is_allowed}")
    print(f"错误详情:")
    for err in response5.errors:
        print(f"  - [{err.reason.value}] {err.field}: {err.message}")
    print(f"\n用户消息:\n{response5.to_user_message()}")
    
    # 测试用例6：便捷函数测试
    print("\n" + "=" * 60)
    print("\n[测试用例6] 便捷函数测试")
    errors6 = ["任务ID不能为空"]
    response6 = intercept_task(errors6, "TASK-001")
    print(f"便捷函数调用成功")
    print(f"拒绝级别: {response6.level.value}")
    print(f"是否允许: {response6.is_allowed}")
    
    # 测试用例7：to_dict方法测试
    print("\n" + "=" * 60)
    print("\n[测试用例7] to_dict方法测试")
    response7 = interceptor.intercept(["Target的描述不能为空"])
    dict_output = response7.to_dict()
    print(f"转换为字典成功")
    print(f"字典内容: {dict_output}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_task_interceptor()
