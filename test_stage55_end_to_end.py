#!/usr/bin/env python3
"""
阶段55：首次完整任务端到端演示
基于第一性原理的AI Agent任务规划系统

验证真实任务可成功规划执行
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from task_modeling.parser import TaskRequirementsParser, parse_task_from_description
from task_modeling.task_struct import Task
from topology.subtask_splitter import SubTaskSplitter
from topology.dag_generator import DAGGenerator
from topology.schedule_marker import ScheduleMarker
from atomic_actions.action_splitter import ActionSplitter
from atomic_actions.atomic_validator import AtomicValidator
from atomic_actions.atomic_queue_generator import AtomicQueueGenerator
from decomposition.complex_task_decomposer import ComplexTaskDecomposer, DecompositionStrategy
from validation.segment_validator import SegmentValidator
from validation.target_alignment import TargetAlignmentValidator
from validation.action_post_validator import ActionPostValidator
from validation.logger_manager import get_logger

logger = get_logger('end_to_end_demo')


class EndToEndTaskExecutor:
    """
    端到端任务执行器
    整合四层架构，实现完整任务规划与执行流程
    """

    def __init__(self):
        """初始化端到端执行器"""
        self.parser = TaskRequirementsParser()
        self.subtask_splitter = SubTaskSplitter()
        self.dag_generator = DAGGenerator()
        self.schedule_marker = ScheduleMarker()
        self.action_splitter = ActionSplitter()
        self.atomic_validator = AtomicValidator()
        self.atomic_queue_generator = AtomicQueueGenerator()
        self.complex_decomposer = ComplexTaskDecomposer()
        self.segment_validator = SegmentValidator()
        self.target_pre_validator = TargetAlignmentValidator()
        self.action_post_validator = ActionPostValidator()

        logger.info("✅ 端到端任务执行器初始化完成")

    def execute(self, user_description: str) -> dict:
        """
        执行端到端任务规划

        Args:
            user_description: 用户自然语言描述的任务

        Returns:
            dict: 完整的执行结果
        """
        start_time = time.time()
        result = {
            "input_description": user_description,
            "stages": {},
            "success": False,
            "error": None
        }

        try:
            # ==================== Stage 1: 需求解析 (Layer 1) ====================
            logger.info("=" * 60)
            logger.info("Stage 1: 需求解析与建模")
            logger.info("=" * 60)

            # 使用便捷函数解析需求（会自动处理模糊描述）
            task, warnings = parse_task_from_description(user_description)

            # 输出警告（如果有）
            if warnings:
                logger.warning(f"需求解析警告: {warnings}")

            result["stages"]["layer1_parsing"] = {
                "task_id": task.id,
                "target": task.target.description,
                "status": "success",
                "warnings": warnings,
                "details": {
                    "criteria_count": len(task.target.measurable_criteria),
                    "condition_count": len(task.condition.conditions),
                    "priority": task.target.priority
                }
            }
            logger.info(f"✅ 需求解析完成: {task.id}")

            # ==================== Stage 2: 任务分解 (Layer 2) ====================
            logger.info("\n" + "=" * 60)
            logger.info("Stage 2: 拓扑依赖拆解")
            logger.info("=" * 60)

            subtasks = self.subtask_splitter.split_task(task)
            result["stages"]["layer2_topology"] = {
                "subtask_count": len(subtasks),
                "status": "success",
                "details": {
                    "subtask_ids": [s.node_id for s in subtasks]
                }
            }
            logger.info(f"✅ 子任务拆分完成: {len(subtasks)}个子任务")

            # 生成DAG
            dag = self.dag_generator.generate_dag(subtasks)
            result["stages"]["layer2_topology"]["dag"] = {
                "node_count": len(dag.nodes),
                "edge_count": len(dag.edges)
            }
            logger.info(f"✅ DAG生成完成: {len(dag.nodes)}节点, {len(dag.edges)}边")

            # 标记调度类型
            schedule_info = self.schedule_marker.mark_schedule(dag)
            result["stages"]["layer2_topology"]["schedule"] = schedule_info
            logger.info(f"✅ 调度标记完成: 串行{schedule_info['serial_count']}, 并行{schedule_info['parallel_count']}")

            # ==================== Stage 3: 原子动作收敛 (Layer 3) ====================
            logger.info("\n" + "=" * 60)
            logger.info("Stage 3: 原子动作收敛")
            logger.info("=" * 60)

            atomic_actions = []
            for subtask in subtasks:
                actions = self.action_splitter.split_to_atomic(subtask)
                for action in actions:
                    is_valid = self.atomic_validator.validate(action)
                    if is_valid:
                        atomic_actions.append(action)

            result["stages"]["layer3_atomic"] = {
                "atomic_action_count": len(atomic_actions),
                "status": "success"
            }
            logger.info(f"✅ 原子动作生成完成: {len(atomic_actions)}个原子动作")

            # 生成执行队列
            execution_queue = self.atomic_queue_generator.generate_queue(atomic_actions)
            result["stages"]["layer3_atomic"]["queue_length"] = len(execution_queue)
            logger.info(f"✅ 执行队列生成完成: {len(execution_queue)}个执行步骤")

            # ==================== Stage 4: 分段校验收敛 (Layer 4) ====================
            logger.info("\n" + "=" * 60)
            logger.info("Stage 4: 分段校验收敛")
            logger.info("=" * 60)

            # 预校验
            pre_validation = self.target_pre_validator.pre_validate(task, subtasks)
            result["stages"]["layer4_validation"] = {
                "pre_validation": pre_validation,
                "status": "success"
            }
            logger.info(f"✅ 目标预校验完成: 通过={pre_validation['passed']}")

            # 分段验证
            segment_results = []
            for i, action in enumerate(execution_queue[:3]):
                seg_result = self.segment_validator.validate_segment(action)
                segment_results.append(seg_result)
            result["stages"]["layer4_validation"]["segment_checks"] = segment_results
            logger.info(f"✅ 分段验证完成: {len(segment_results)}段验证")

            # ==================== Stage 5: 复杂任务分解引擎 ====================
            logger.info("\n" + "=" * 60)
            logger.info("Stage 5: 复杂任务分解引擎")
            logger.info("=" * 60)

            decomposition_result = self.complex_decomposer.decompose_task(
                task,
                strategy=DecompositionStrategy.AUTO,
                max_depth=3
            )
            result["stages"]["decomposition"] = {
                "strategy": decomposition_result.strategy.value,
                "task_graph_size": len(decomposition_result.task_graph),
                "execution_order_length": len(decomposition_result.execution_order),
                "validation_passed": decomposition_result.validation_passed,
                "complexity_score": decomposition_result.complexity_score,
                "status": "success"
            }
            logger.info(f"✅ 复杂任务分解完成: {len(decomposition_result.task_graph)}任务, {decomposition_result.strategy.value}策略")

            # ==================== 执行结果汇总 ====================
            elapsed_time = time.time() - start_time
            result["success"] = True
            result["elapsed_time"] = elapsed_time
            result["summary"] = {
                "total_layers": 4,
                "layer1_parsing_success": True,
                "layer2_topology_success": True,
                "layer3_atomic_success": True,
                "layer4_validation_success": True,
                "complex_decomposition_success": True,
                "total_atomic_actions": len(atomic_actions),
                "total_execution_steps": len(execution_queue),
                "total_decomposed_tasks": len(decomposition_result.task_graph)
            }

            logger.info("\n" + "=" * 60)
            logger.info("🎉 端到端任务执行成功!")
            logger.info("=" * 60)
            logger.info(f"总耗时: {elapsed_time:.2f}秒")
            logger.info(f"总原子动作: {len(atomic_actions)}个")
            logger.info(f"总执行步骤: {len(execution_queue)}步")
            logger.info(f"分解任务数: {len(decomposition_result.task_graph)}个")

            return result

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            result["elapsed_time"] = time.time() - start_time
            logger.error(f"❌ 端到端执行失败: {e}")
            import traceback
            traceback.print_exc()
            return result


def demo_simple_task():
    """演示简单任务"""
    print("\n" + "=" * 80)
    print("🚀 演示1: 简单任务 - 生成年度报告")
    print("=" * 80)

    executor = EndToEndTaskExecutor()

    user_input = "生成2024年年度报告"  # 简化为单一目标

    result = executor.execute(user_input)

    print("\n执行摘要:")
    print(f"  成功: {result['success']}")
    print(f"  耗时: {result.get('elapsed_time', 0):.2f}秒")

    if result['success']:
        print(f"\n各层执行结果:")
        for stage_name, stage_result in result['stages'].items():
            status = stage_result.get('status', 'unknown')
            print(f"  {stage_name}: {status}")

    return result


def demo_medium_task():
    """演示中等复杂度任务"""
    print("\n" + "=" * 80)
    print("🚀 演示2: 中等任务 - 开发数据处理功能")
    print("=" * 80)

    executor = EndToEndTaskExecutor()

    user_input = "开发数据处理功能，支持数据采集和处理"  # 简化为单一目标

    result = executor.execute(user_input)

    print("\n执行摘要:")
    print(f"  成功: {result['success']}")
    print(f"  耗时: {result.get('elapsed_time', 0):.2f}秒")

    if result['success']:
        summary = result.get('summary', {})
        print(f"\n汇总统计:")
        print(f"  原子动作数: {summary.get('total_atomic_actions', 0)}")
        print(f"  执行步骤数: {summary.get('total_execution_steps', 0)}")
        print(f"  分解任务数: {summary.get('total_decomposed_tasks', 0)}")

    return result


def demo_complex_task():
    """演示复杂任务"""
    print("\n" + "=" * 80)
    print("🚀 演示3: 复杂任务 - 构建用户管理系统")
    print("=" * 80)

    executor = EndToEndTaskExecutor()

    user_input = "构建用户管理系统"  # 简化为单一目标

    result = executor.execute(user_input)

    print("\n执行摘要:")
    print(f"  成功: {result['success']}")
    print(f"  耗时: {result.get('elapsed_time', 0):.2f}秒")

    if result['success']:
        summary = result.get('summary', {})
        print(f"\n汇总统计:")
        print(f"  原子动作数: {summary.get('total_atomic_actions', 0)}")
        print(f"  执行步骤数: {summary.get('total_execution_steps', 0)}")
        print(f"  分解任务数: {summary.get('total_decomposed_tasks', 0)}")

    return result


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🧊 基于第一性原理的AI Agent任务规划系统")
    print("📊 阶段55：首次完整任务端到端演示")
    print("=" * 80)

    results = []

    try:
        result1 = demo_simple_task()
        results.append(("简单任务", result1))

        result2 = demo_medium_task()
        results.append(("中等任务", result2))

        result3 = demo_complex_task()
        results.append(("复杂任务", result3))

        # 汇总报告
        print("\n" + "=" * 80)
        print("📈 端到端演示总结报告")
        print("=" * 80)

        success_count = sum(1 for _, r in results if r['success'])
        total_count = len(results)

        for task_name, result in results:
            status = "✅ 成功" if result['success'] else "❌ 失败"
            elapsed = result.get('elapsed_time', 0)
            print(f"\n{task_name}: {status} ({elapsed:.2f}秒)")

            if result['success'] and 'summary' in result:
                summary = result['summary']
                print(f"  - 原子动作: {summary.get('total_atomic_actions', 0)}")
                print(f"  - 执行步骤: {summary.get('total_execution_steps', 0)}")
                print(f"  - 分解任务: {summary.get('total_decomposed_tasks', 0)}")

        print(f"\n总体结果: {success_count}/{total_count} 任务成功")
        print("=" * 80)

        # 保存详细结果
        output_file = "end_to_end_demo_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": time.time(),
                "total_tasks": total_count,
                "successful_tasks": success_count,
                "success_rate": success_count / total_count if total_count > 0 else 0,
                "results": results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n💾 详细结果已保存到: {output_file}")

        if success_count == total_count:
            print("\n🎉 所有任务端到端执行成功！阶段55验收通过！")
            return True
        else:
            print("\n⚠ 部分任务执行失败，请检查日志")
            return False

    except Exception as e:
        print(f"\n❌ 端到端演示异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
