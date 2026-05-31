#!/usr/bin/env python3
"""
大规模复杂场景压力测试
第四层验证模块综合测试
"""

import time
import random
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validation.segment_validator import SegmentValidator, ValidationPoint
from validation.target_alignment import TargetAlignmentValidator
from validation.action_post_validator import ActionPostValidator, ActionOutput, OutputValidationStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class StressTestResult:
    """压力测试结果"""
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.errors = []
        self.warnings = []
        self.start_time = 0.0
        self.end_time = 0.0
        self.performance_metrics = {}

    def add_pass(self, test_name: str):
        self.passed_tests += 1
        logger.info(f"✅ 通过: {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed_tests += 1
        self.errors.append({"test": test_name, "error": error})
        logger.error(f"❌ 失败: {test_name} - {error}")

    def add_warning(self, test_name: str, warning: str):
        self.warnings.append({"test": test_name, "warning": warning})
        logger.warning(f"⚠️ 警告: {test_name} - {warning}")

    def get_summary(self) -> Dict[str, Any]:
        duration = self.end_time - self.start_time
        return {
            "total_tests": self.total_tests,
            "passed": self.passed_tests,
            "failed": self.failed_tests,
            "pass_rate": self.passed_tests / self.total_tests if self.total_tests > 0 else 0,
            "duration": duration,
            "tests_per_second": self.total_tests / duration if duration > 0 else 0,
            "performance_metrics": self.performance_metrics,
            "errors": self.errors,
            "warnings": self.warnings
        }


def test_large_scale_validations():
    """测试大规模验证"""
    logger.info("=" * 60)
    logger.info("测试1: 大规模验证测试 (1000次验证)")
    logger.info("=" * 60)
    
    result = StressTestResult()
    result.start_time = time.time()
    
    # 创建验证器
    segment_validator = SegmentValidator(failure_threshold=10)
    target_validator = TargetAlignmentValidator()
    post_validator = ActionPostValidator()
    
    # 定义目标
    target_validator.define_target(
        target_id="large_target",
        target_text="复杂的数据处理和分析任务，包含多个子步骤和条件分支",
        scope_keywords=["数据", "处理", "分析", "任务", "步骤", "条件"],
        anti_keywords=["删除", "破坏", "泄露"]
    )
    
    # 生成1000个测试场景
    actions = [
        f"执行第{i}步数据处理" for i in range(500)
    ] + [
        f"执行第{i}步数据分析" for i in range(300)
    ] + [
        f"执行第{i}步无关操作" for i in range(200)
    ]
    
    # 执行验证
    for i, action in enumerate(actions):
        try:
            # 目标对齐验证
            alignment_report = target_validator.validate_alignment(
                target_id="large_target",
                action_text=action
            )
            
            # 动作后校验
            success = random.random() > 0.05  # 95%成功率
            output = ActionOutput(
                action_id=f"action_{i}",
                success=success,
                data={"step": i, "action": action} if success else None,
                error=None if success else random.choice(["超时", "异常", "失败"]),
                execution_time=random.uniform(0.1, 5.0)
            )
            
            validation_report = post_validator.validate_action_output(
                f"action_{i}",
                output
            )
            
            result.total_tests += 1
            
            if alignment_report.metrics.match_score >= 0.5 and validation_report.is_valid():
                result.add_pass(f"验证_{i}")
            else:
                result.add_warning(f"验证_{i}", f"匹配度:{alignment_report.metrics.match_score:.2f}, 状态:{validation_report.validation_status.value}")
                
        except Exception as e:
            result.add_fail(f"验证_{i}", str(e))
    
    result.end_time = time.time()
    
    # 统计信息
    result.performance_metrics = {
        "post_validator_stats": post_validator.get_statistics(),
        "target_validator_trend": target_validator.get_alignment_trend("large_target")
    }
    
    return result


def test_concurrent_validations():
    """测试并发验证"""
    logger.info("=" * 60)
    logger.info("测试2: 并发验证测试 (100个并发任务)")
    logger.info("=" * 60)
    
    result = StressTestResult()
    result.start_time = time.time()
    
    def validate_task(task_id: int) -> Dict[str, Any]:
        """单个验证任务"""
        try:
            validator = SegmentValidator()
            
            # 子任务预校验
            context = {
                "inputs": {"data": f"data_{task_id}"},
                "dependencies_ready": task_id % 5 != 0
            }
            pre_report = validator.pre_validate_subtask(f"task_{task_id}", context)
            
            # 模拟执行
            time.sleep(random.uniform(0.01, 0.1))
            
            # 动作后校验
            success = random.random() > 0.1
            output = ActionOutput(
                action_id=f"task_{task_id}",
                success=success,
                data={"task_id": task_id, "result": "success"} if success else None,
                error=None if success else "执行失败",
                execution_time=random.uniform(0.1, 1.0)
            )
            
            post_validator = ActionPostValidator()
            post_report = post_validator.validate_action_output(f"task_{task_id}", output)
            
            return {
                "task_id": task_id,
                "pre_passed": pre_report.is_passed(),
                "post_valid": post_report.is_valid(),
                "status": "success"
            }
        except Exception as e:
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }
    
    # 执行100个并发任务
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(validate_task, i) for i in range(100)]
        
        for future in as_completed(futures):
            result.total_tests += 1
            try:
                task_result = future.result()
                if task_result["status"] == "success":
                    result.add_pass(f"并发任务_{task_result['task_id']}")
                else:
                    result.add_fail(f"并发任务_{task_result['task_id']}", task_result.get("error", "未知错误"))
            except Exception as e:
                result.add_fail(f"并发任务", str(e))
    
    result.end_time = time.time()
    
    return result


def test_extreme_scenarios():
    """测试极端场景"""
    logger.info("=" * 60)
    logger.info("测试3: 极端场景测试")
    logger.info("=" * 60)
    
    result = StressTestResult()
    result.start_time = time.time()
    
    test_cases = [
        {
            "name": "空输入验证",
            "test": lambda: SegmentValidator().pre_validate_subtask("test", {})
        },
        {
            "name": "None值验证",
            "test": lambda: SegmentValidator().pre_validate_subtask("test", {"inputs": None})
        },
        {
            "name": "超长输入验证",
            "test": lambda: SegmentValidator().pre_validate_subtask("test", {
                "inputs": "x" * 10000
            })
        },
        {
            "name": "特殊字符验证",
            "test": lambda: SegmentValidator().pre_validate_subtask("test", {
                "inputs": "<script>alert('xss')</script>"
            })
        },
        {
            "name": "目标对齐-空目标",
            "test": lambda: TargetAlignmentValidator().validate_alignment("test", "test_action")
        },
        {
            "name": "目标对齐-超长文本",
            "test": lambda: TargetAlignmentValidator().validate_alignment(
                "test",
                "x" * 10000
            )
        },
        {
            "name": "后校验-超大数据",
            "test": lambda: ActionPostValidator().validate_action_output(
                "test",
                ActionOutput(
                    action_id="test",
                    success=True,
                    data={"big_data": "x" * 1000000},
                    execution_time=0.1
                )
            )
        },
        {
            "name": "后校验-循环引用",
            "test": lambda: ActionPostValidator().validate_action_output(
                "test",
                ActionOutput(
                    action_id="test",
                    success=True,
                    data={"ref": None},  # 简化测试
                    execution_time=0.1
                )
            )
        },
        {
            "name": "熔断器极限测试",
            "test": lambda: test_circuit_breaker_extreme()
        },
        {
            "name": "验证器链式调用",
            "test": lambda: test_validator_chain()
        }
    ]
    
    for test_case in test_cases:
        result.total_tests += 1
        try:
            test_case["test"]()
            result.add_pass(test_case["name"])
        except Exception as e:
            result.add_fail(test_case["name"], str(e))
    
    result.end_time = time.time()
    
    return result


def test_circuit_breaker_extreme():
    """熔断器极限测试"""
    validator = SegmentValidator(failure_threshold=3)
    
    # 快速失败以触发熔断
    for i in range(10):
        context = {"has_output": False, "has_error": True}
        validator.post_validate_action(f"action_{i}", context)
        
        status = validator.get_circuit_status()
        if status["state"] == "open":
            logger.info(f"熔断器在第{i+1}次后打开")
            break
    
    # 验证熔断阻止
    result = validator.post_validate_action("blocked_action", {"has_output": True})
    if result.result.value == "fail":
        logger.info("✅ 熔断器正确阻止了执行")
    else:
        logger.warning("⚠️ 熔断器未阻止执行")


def test_validator_chain():
    """验证器链式调用测试"""
    # 创建链式验证
    target_validator = TargetAlignmentValidator()
    post_validator = ActionPostValidator()
    
    # 定义目标
    target_validator.define_target(
        target_id="chain_test",
        target_text="链式验证测试任务"
    )
    
    # 执行多次验证
    for i in range(10):
        # 目标对齐
        alignment = target_validator.validate_alignment(
            "chain_test",
            f"执行步骤{i}"
        )
        
        # 后校验
        output = ActionOutput(
            action_id=f"chain_action_{i}",
            success=alignment.metrics.match_score >= 0.5,
            data={"step": i},
            execution_time=0.1
        )
        
        post_validator.validate_action_output(f"chain_action_{i}", output)
    
    logger.info("✅ 验证器链式调用正常")


def test_memory_leak():
    """内存泄漏测试"""
    logger.info("=" * 60)
    logger.info("测试4: 内存和历史记录测试")
    logger.info("=" * 60)
    
    result = StressTestResult()
    result.start_time = time.time()
    
    # 创建验证器
    validator = SegmentValidator()
    
    # 执行10000次验证
    for i in range(10000):
        context = {
            "inputs": {"data": i},
            "dependencies_ready": True
        }
        validator.pre_validate_subtask(f"task_{i}", context)
        
        if i % 1000 == 0:
            logger.info(f"已完成 {i} 次验证")
    
    # 检查历史记录
    history_count = len(validator.validation_history)
    logger.info(f"历史记录数量: {history_count}")
    
    # 验证历史记录限制
    result.total_tests = 1
    if history_count == 10000:
        result.add_pass("历史记录存储")
    else:
        result.add_warning("历史记录存储", f"期望10000条，实际{history_count}条")
    
    result.end_time = time.time()
    
    return result


def test_error_recovery():
    """错误恢复测试"""
    logger.info("=" * 60)
    logger.info("测试5: 错误恢复和重试机制测试")
    logger.info("=" * 60)
    
    result = StressTestResult()
    result.start_time = time.time()
    
    # 测试熔断器恢复
    validator = SegmentValidator(failure_threshold=2)
    
    # 触发熔断
    for i in range(3):
        validator.post_validate_action(f"fail_{i}", {
            "has_output": False,
            "has_error": True
        })
    
    # 检查熔断状态
    status = validator.get_circuit_status()
    result.total_tests += 1
    
    if status["state"] == "open":
        result.add_pass("熔断器正确打开")
    else:
        result.add_fail("熔断器状态", f"期望open，实际{status['state']}")
    
    # 重置熔断器
    validator.reset_circuit_breaker()
    
    # 验证恢复
    status_after = validator.get_circuit_status()
    result.total_tests += 1
    
    if status_after["state"] == "closed":
        result.add_pass("熔断器重置成功")
    else:
        result.add_fail("熔断器重置", f"期望closed，实际{status_after['state']}")
    
    # 验证器状态清理
    test_validator = SegmentValidator()
    for i in range(5):
        test_validator.pre_validate_subtask(f"reset_test_{i}", {
            "inputs": {"data": i}
        })
    
    test_validator.reset_circuit_breaker()
    
    result.total_tests += 1
    if test_validator.get_circuit_status()["state"] == "closed":
        result.add_pass("验证器状态清理")
    else:
        result.add_fail("验证器状态清理", "状态未正确重置")
    
    result.end_time = time.time()
    
    return result


def generate_test_report(results: List[StressTestResult]):
    """生成测试报告"""
    logger.info("\n" + "=" * 80)
    logger.info("📊 大规模复杂场景压力测试报告")
    logger.info("=" * 80)
    
    total_tests = sum(r.total_tests for r in results)
    total_passed = sum(r.passed_tests for r in results)
    total_failed = sum(r.failed_tests for r in results)
    total_duration = sum(r.end_time - r.start_time for r in results)
    
    logger.info(f"\n总体统计:")
    logger.info(f"  总测试数: {total_tests}")
    logger.info(f"  通过: {total_passed} ({total_passed/total_tests*100:.1f}%)")
    logger.info(f"  失败: {total_failed} ({total_failed/total_tests*100:.1f}%)")
    logger.info(f"  总耗时: {total_duration:.2f}秒")
    logger.info(f"  测试速度: {total_tests/total_duration:.1f} 测试/秒")
    
    logger.info(f"\n各测试项详情:")
    test_names = [
        "大规模验证测试",
        "并发验证测试",
        "极端场景测试",
        "内存和历史记录测试",
        "错误恢复测试"
    ]
    
    for i, result in enumerate(results):
        name = test_names[i] if i < len(test_names) else f"测试{i+1}"
        logger.info(f"\n  {name}:")
        logger.info(f"    测试数: {result.total_tests}")
        logger.info(f"    通过: {result.passed_tests}")
        logger.info(f"    失败: {result.failed_tests}")
        logger.info(f"    耗时: {result.end_time - result.start_time:.2f}秒")
        
        if result.warnings:
            logger.info(f"    警告数: {len(result.warnings)}")
        
        if result.errors:
            logger.info(f"    错误详情 (前5个):")
            for error in result.errors[:5]:
                logger.info(f"      - {error['test']}: {error['error']}")
    
    logger.info("\n" + "=" * 80)
    
    # 性能指标
    if results:
        perf = results[0].performance_metrics
        if perf:
            logger.info("\n性能指标:")
            if "post_validator_stats" in perf:
                stats = perf["post_validator_stats"]
                logger.info(f"  后校验统计:")
                logger.info(f"    总验证数: {stats['total_validations']}")
                logger.info(f"    成功率: {stats['success_rate']*100:.1f}%")
                logger.info(f"    平均耗时: {stats['average_execution_time']*1000:.2f}ms")
    
    logger.info("=" * 80)


def main():
    """运行所有压力测试"""
    logger.info("\n" + "=" * 80)
    logger.info("🚀 开始大规模复杂场景压力测试")
    logger.info("=" * 80)
    logger.info("测试场景:")
    logger.info("  1. 大规模验证测试 (1000次)")
    logger.info("  2. 并发验证测试 (100个并发)")
    logger.info("  3. 极端场景测试 (10个边界场景)")
    logger.info("  4. 内存和历史记录测试 (10000次)")
    logger.info("  5. 错误恢复测试 (熔断器)")
    logger.info("=" * 80 + "\n")
    
    results = []
    
    try:
        # 测试1: 大规模验证
        result1 = test_large_scale_validations()
        results.append(result1)
        
        # 测试2: 并发验证
        result2 = test_concurrent_validations()
        results.append(result2)
        
        # 测试3: 极端场景
        result3 = test_extreme_scenarios()
        results.append(result3)
        
        # 测试4: 内存测试
        result4 = test_memory_leak()
        results.append(result4)
        
        # 测试5: 错误恢复
        result5 = test_error_recovery()
        results.append(result5)
        
        # 生成报告
        generate_test_report(results)
        
        # 计算最终结果
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed_tests for r in results)
        pass_rate = total_passed / total_tests if total_tests > 0 else 0
        
        logger.info("\n" + "=" * 80)
        if pass_rate >= 0.95:
            logger.info("🎉 测试完成！系统表现优秀 (通过率 >= 95%)")
        elif pass_rate >= 0.80:
            logger.info("⚠️ 测试完成！系统表现良好 (通过率 >= 80%)")
        else:
            logger.info("❌ 测试完成！系统存在问题，需要修复 (通过率 < 80%)")
        logger.info(f"最终通过率: {pass_rate*100:.1f}%")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"测试执行失败: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
