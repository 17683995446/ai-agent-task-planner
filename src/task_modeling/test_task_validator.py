"""
任务合法性校验器测试
基于第一性原理的AI Agent任务规划系统
"""

from task_validator import TaskValidator, validate_task, validate_task_or_raise, TaskValidationError
from task_struct import (
    Task, Target, Condition, ConditionItem, Boundary, ScopeBoundary, 
    ResourceBoundary, EndRule, SuccessCondition, FailureCondition,
    MeasurableCriterion, TaskStatus
)


def test_task_validator():
    """测试任务合法性校验器"""
    print("=" * 60)
    print("任务合法性校验器测试")
    print("=" * 60)
    
    validator = TaskValidator()
    
    # 测试用例1：完整的合法任务
    print("\n[测试用例1] 完整的合法任务")
    try:
        task1 = create_valid_task()
        is_valid, errors = validator.validate(task1)
        if is_valid:
            print("✓ 任务校验通过")
        else:
            print(f"✗ 任务校验失败，共{len(errors)}个错误:")
            for err in errors:
                print(f"  - {err}")
    except Exception as e:
        print(f"✗ 测试异常: {e}")
    
    # 测试用例2：缺少Target描述
    print("\n[测试用例2] 缺少Target描述")
    try:
        task2 = create_valid_task()
        task2.target.description = ""
        is_valid, errors = validator.validate(task2)
        if not is_valid:
            print(f"✓ 正确检测到错误: {errors}")
        else:
            print("✗ 应该检测到错误但没有")
    except Exception as e:
        print(f"✗ 测试异常: {e}")
    
    # 测试用例3：缺少前置条件
    print("\n[测试用例3] 缺少前置条件")
    try:
        task3 = create_valid_task()
        task3.condition.conditions = []
        is_valid, errors = validator.validate(task3)
        if not is_valid:
            print(f"✓ 正确检测到错误: {errors}")
        else:
            print("✗ 应该检测到错误但没有")
    except Exception as e:
        print(f"✗ 测试异常: {e}")
    
    # 测试用例4：优先级超出范围
    print("\n[测试用例4] 优先级超出范围")
    try:
        task4 = create_valid_task()
        task4.target.priority = 15
        is_valid, errors = validator.validate(task4)
        if not is_valid:
            print(f"✓ 正确检测到错误: {errors}")
        else:
            print("✗ 应该检测到错误但没有")
    except Exception as e:
        print(f"✗ 测试异常: {e}")
    
    # 测试用例5：缺少成功条件
    print("\n[测试用例5] 缺少成功条件")
    try:
        task5 = create_valid_task()
        task5.end_rule.success_conditions = []
        is_valid, errors = validator.validate(task5)
        if not is_valid:
            print(f"✓ 正确检测到错误: {errors}")
        else:
            print("✗ 应该检测到错误但没有")
    except Exception as e:
        print(f"✗ 测试异常: {e}")
    
    # 测试用例6：便捷函数测试
    print("\n[测试用例6] 便捷函数测试")
    try:
        task6 = create_valid_task()
        is_valid, errors = validate_task(task6)
        if is_valid:
            print("✓ 便捷函数正常工作")
        else:
            print(f"✗ 便捷函数异常: {errors}")
    except Exception as e:
        print(f"✗ 测试异常: {e}")
    
    # 测试用例7：便捷函数异常抛出测试
    print("\n[测试用例7] 便捷函数异常抛出测试")
    try:
        task7 = create_valid_task()
        task7.target.description = ""
        validate_task_or_raise(task7)
        print("✗ 应该抛出异常但没有")
    except TaskValidationError as e:
        print(f"✓ 正确抛出TaskValidationError: {e.errors}")
    except Exception as e:
        print(f"✗ 抛出了意外异常: {e}")
    
    # 测试用例8：validate_or_raise方法测试
    print("\n[测试用例8] validate_or_raise方法测试")
    try:
        task8 = create_valid_task()
        validator.validate_or_raise(task8)
        print("✓ validate_or_raise方法正常工作")
    except TaskValidationError as e:
        print(f"✗ 不应该抛出异常: {e}")
    except Exception as e:
        print(f"✗ 抛出了意外异常: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


def create_valid_task() -> Task:
    """创建一个有效的测试任务"""
    target = Target(
        id="T-TEST-001",
        description="测试任务目标",
        measurable_criteria=[
            MeasurableCriterion(
                id="MC-001",
                description="测试标准",
                type="boolean",
                threshold=True
            )
        ],
        priority=5
    )
    
    condition = Condition(
        conditions=[
            ConditionItem(
                id="C-001",
                description="测试前置条件",
                type="existence",
                check_rule="True"
            )
        ],
        logical_operator="AND"
    )
    
    boundary = Boundary(
        scope=ScopeBoundary(
            inclusions=["测试范围"],
            exclusions=[]
        ),
        resources=ResourceBoundary(
            max_time_seconds=3600.0,
            max_iterations=10
        )
    )
    
    end_rule = EndRule(
        success_conditions=[
            SuccessCondition(
                id="SC-001",
                description="测试成功条件",
                check_rule="True"
            )
        ],
        failure_conditions=[
            FailureCondition(
                id="FC-001",
                description="测试失败条件",
                check_rule="False",
                priority=1
            )
        ]
    )
    
    return Task(
        id="TASK-001",
        target=target,
        condition=condition,
        boundary=boundary,
        end_rule=end_rule
    )


if __name__ == "__main__":
    test_task_validator()
