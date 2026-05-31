#!/usr/bin/env python3
"""
阶段54测试：复杂任务分解引擎
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from decomposition.complex_task_decomposer import (
    ComplexTaskDecomposer,
    DecompositionStrategy,
    TaskComplexity,
    DecompositionResult,
    decompose_task_simple
)
from task_modeling.task_struct import (
    Task, Target, Condition, Boundary, EndRule,
    MeasurableCriterion, ConditionItem, ScopeBoundary,
    ResourceBoundary, QualityBoundary, SuccessCondition
)
from validation.logger_manager import get_logger

logger = get_logger('test.decomposition')


def create_test_task(name: str, complexity_level: int) -> Task:
    """创建不同复杂度的测试任务"""
    
    # 简化版 - 不使用递归Target引用
    target = Target(
        id=f"t_{name}",
        description=f"完成任务: {name}",
        measurable_criteria=[
            MeasurableCriterion(
                id="c_main",
                description="任务完成",
                type="boolean",
                threshold=True
            )
        ],
        priority=5
    )
    
    condition = Condition(
        conditions=[
            ConditionItem(
                id=f"cond_{name}",
                description="环境准备就绪",
                type="state",
                check_rule="is_env_ready()",
                required=True
            )
        ],
        logical_operator="AND"
    )
    
    boundary = Boundary(
        scope=ScopeBoundary(
            inclusions=["核心功能"],
            exclusions=["非核心功能"]
        ),
        resources=ResourceBoundary(
            max_time_seconds=86400 * complexity_level,
            max_cost=1000 * complexity_level
        )
    )
    
    end_rule = EndRule(
        success_conditions=[
            SuccessCondition(
                id=f"ac_{name}",
                description="所有目标达成",
                check_rule="all_targets_achieved()"
            )
        ],
        failure_conditions=[],
        evaluation_logic="success: (all); failure: ()"
    )
    
    task = Task(
        id=f"test_task_{name}",
        target=target,
        condition=condition,
        boundary=boundary,
        end_rule=end_rule
    )
    
    return task


def test_strategy_selection():
    """测试策略选择"""
    print("\n" + "=" * 60)
    print("测试1: 策略选择")
    print("=" * 60)
    
    decomposer = ComplexTaskDecomposer()
    
    # 测试不同复杂度任务
    for level, name in [(1, "简单"), (2, "中等"), (3, "复杂")]:
        task = create_test_task(name, level)
        result = decomposer.decompose_task(task)
        
        print(f"\n{name}任务:")
        print(f"  分解为 {len(result.task_graph)} 个任务")
        print(f"  执行步骤: {len(result.execution_order)}")
        print(f"  验证通过: {result.validation_passed}")
    
    return True


def test_decomposition_result():
    """测试分解结果"""
    print("\n" + "=" * 60)
    print("测试2: 分解结果")
    print("=" * 60)
    
    decomposer = ComplexTaskDecomposer()
    task = create_test_task("result_test", 2)
    
    result = decomposer.decompose_task(task, strategy=DecompositionStrategy.TREE, max_depth=2)
    
    print(f"\n任务图: {len(result.task_graph)} 个任务")
    print(f"执行顺序: {len(result.execution_order)} 步骤")
    
    # 查看部分执行顺序
    print(f"\n前5个任务:")
    for i, task_id in enumerate(result.execution_order[:5]):
        node = result.task_graph[task_id]
        print(f"  {i+1}. {node.name}")
    
    # 保存结果
    output_file = "decomposition_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到 {output_file}")
    return True


def main():
    """运行测试"""
    print("\n" + "=" * 80)
    print("🚀 阶段54测试：复杂任务分解引擎")
    print("=" * 80)
    
    try:
        test_strategy_selection()
        test_decomposition_result()
        
        print("\n🎉 阶段54测试成功！")
        return True
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
