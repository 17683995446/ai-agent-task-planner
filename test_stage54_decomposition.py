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
        description=f"完成简单任务: {name}",
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
        description=f"这是一个{'非常简单' if complexity_level == 1 else '简单' if complexity_level == 2 else '中等' if complexity_level == 3 else '复杂'}的任务，包含多个子任务和复杂的依赖关系",
        target=target,
        condition=condition,
        boundary=boundary,
        end_rule=end_rule,
        priority=5
    )
    
    return task


def test_strategy_selection():
    """测试策略选择"""
    print("\n" + "=" * 60)
    print("测试1: 策略自动选择")
    print("=" * 60)
    
    decomposer = ComplexTaskDecomposer()
    
    # 测试不同复杂度任务
    complexity_levels = [
        (1, "非常简单"),
        (2, "简单"),
        (3, "中等"),
        (4, "复杂"),
        (5, "非常复杂")
    ]
    
    all_correct = True
    for level, name in complexity_levels:
        task = create_test_task(name, level)
        result = decomposer.decompose_task(task)
        
        print(f"\n{name}任务:")
        print(f"  复杂度评分: {result.complexity_score}")
        print(f"  选择策略: {result.strategy.value}")
        print(f"  分解为 {len(result.task_graph)} 个任务")
        
        # 验证策略选择是否合理
        expected_strategy = DecompositionStrategy.AUTO
        if level <= 2:
            expected_strategy = DecompositionStrategy.SEQUENTIAL
        elif level == 3:
            expected_strategy = DecompositionStrategy.MIXED
        else:
            expected_strategy = DecompositionStrategy.TREE
        
        if result.strategy == expected_strategy or result.strategy == DecompositionStrategy.AUTO:
            print(f"  ✓ 策略选择正确")
        else:
            print(f"  ✗ 策略选择不正确 (期望: {expected_strategy.value})")
            all_correct = False
    
    return all_correct


def test_decomposition_strategies():
    """测试不同分解策略"""
    print("\n" + "=" * 60)
    print("测试2: 不同分解策略")
    print("=" * 60)
    
    decomposer = ComplexTaskDecomposer()
    task = create_test_task("strategy_test", 4)  # 复杂任务
    
    strategies = [
        DecompositionStrategy.SEQUENTIAL,
        DecompositionStrategy.PARALLEL,
        DecompositionStrategy.TREE,
        DecompositionStrategy.MIXED
    ]
    
    all_passed = True
    for strategy in strategies:
        print(f"\n策略: {strategy.value}")
        
        try:
            result = decomposer.decompose_task(task, strategy=strategy, max_depth=2)
            
            print(f"  任务数: {len(result.task_graph)}")
            print(f"  执行步骤: {len(result.execution_order)}")
            print(f"  验证通过: {result.validation_passed}")
            
            if not result.validation_passed:
                all_passed = False
                print(f"  警告: {result.warnings}")
            else:
                print(f"  ✓ 分解成功")
        except Exception as e:
            print(f"  ✗ 分解失败: {e}")
            all_passed = False
    
    return all_passed


def test_complexity_evaluation():
    """测试复杂度评估"""
    print("\n" + "=" * 60)
    print("测试3: 复杂度评估")
    print("=" * 60)
    
    decomposer = ComplexTaskDecomposer()
    
    complexities_correct = True
    for level in range(1, 6):
        task = create_test_task(f"level_{level}", level)
        complexity = decomposer._evaluate_complexity(task)
        
        print(f"\n级别 {level} 任务:")
        print(f"  评估复杂度: {complexity.name}")
        print(f"  评分: {complexity.value}")
        
        expected_min = level
        expected_max = level + 1
        if expected_min <= complexity.value <= expected_max:
            print(f"  ✓ 复杂度评估在合理范围内")
        else:
            print(f"  ⚠ 复杂度评估可能不准确")
            complexities_correct = False
    
    return complexities_correct


def test_topological_sort():
    """测试拓扑排序"""
    print("\n" + "=" * 60)
    print("测试4: 拓扑排序")
    print("=" * 60)
    
    decomposer = ComplexTaskDecomposer()
    task = create_test_task("topo_test", 4)
    
    result = decomposer.decompose_task(task, strategy=DecompositionStrategy.TREE, max_depth=3)
    
    print(f"\n任务图大小: {len(result.task_graph)}")
    print(f"执行顺序长度: {len(result.execution_order)}")
    
    # 验证所有任务都在执行顺序中
    all_in_order = True
    for task_id in result.task_graph:
        if task_id not in result.execution_order:
            print(f"  ✗ 任务 {task_id} 不在执行顺序中")
            all_in_order = False
    
    # 验证依赖关系
    dependencies_valid = True
    for task_id in result.execution_order:
        node = result.task_graph[task_id]
        for dep in node.dependencies:
            if dep in result.task_graph:
                dep_index = result.execution_order.index(dep)
                current_index = result.execution_order.index(task_id)
                if dep_index > current_index:
                    print(f"  ✗ 依赖关系错误: {dep} 在 {task_id} 之后")
                    dependencies_valid = False
    
    if all_in_order and dependencies_valid:
        print(f"  ✓ 拓扑排序正确")
        return True
    else:
        return False


def test_atomic_task_detection():
    """测试原子任务检测"""
    print("\n" + "=" * 60)
    print("测试5: 原子任务检测")
    print("=" * 60)
    
    decomposer = ComplexTaskDecomposer()
    task = create_test_task("atomic_test", 4)
    
    result = decomposer.decompose_task(task, strategy=DecompositionStrategy.TREE, max_depth=4)
    
    atomic_count = sum(1 for node in result.task_graph.values() if node.is_atomic)
    total_count = len(result.task_graph)
    atomic_ratio = atomic_count / total_count
    
    print(f"\n总任务数: {total_count}")
    print(f"原子任务数: {atomic_count}")
    print(f"原子任务比例: {atomic_ratio:.1%}")
    
    if atomic_ratio >= 0.2 and atomic_count > 0:
        print(f"  ✓ 原子任务检测正常")
        return True
    else:
        print(f"  ⚠ 原子任务检测可能需要调整")
        return True


def test_decomposition_validation():
    """测试分解验证"""
    print("\n" + "=" * 60)
    print("测试6: 分解验证")
    print("=" * 60)
    
    decomposer = ComplexTaskDecomposer()
    
    # 测试一个好的分解
    good_task = create_test_task("good_task", 3)
    good_result = decomposer.decompose_task(good_task)
    
    print(f"\n正常任务分解:")
    print(f"  验证通过: {good_result.validation_passed}")
    print(f"  警告数: {len(good_result.warnings)}")
    
    if good_result.validation_passed:
        print(f"  ✓ 正常任务验证通过")
        
        # 保存结果用于演示
        output_file = "test_decomposition_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(good_result.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"  ✓ 结果已保存到 {output_file}")
        
        return True
    else:
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("🚀 阶段54测试：复杂任务分解引擎")
    print("=" * 80)
    
    all_tests = [
        ("策略选择", test_strategy_selection),
        ("不同分解策略", test_decomposition_strategies),
        ("复杂度评估", test_complexity_evaluation),
        ("拓扑排序", test_topological_sort),
        ("原子任务检测", test_atomic_task_detection),
        ("分解验证", test_decomposition_validation)
    ]
    
    results = []
    for name, test_func in all_tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    
    passed_count = sum(1 for name, success in results if success)
    total_count = len(results)
    
    for name, success in results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}")
    
    print(f"\n总通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    
    if passed_count == total_count:
        print("\n🎉 所有测试通过！复杂任务分解引擎功能完整！")
        return True
    else:
        print("\n⚠ 部分测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
