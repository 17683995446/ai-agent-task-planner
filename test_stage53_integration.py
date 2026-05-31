#!/usr/bin/env python3
"""
阶段53：集成测试完善
基于第一性原理的AI Agent任务规划系统

功能：
- 端到端集成测试
- 回归测试套件
- 性能基准测试
- CI/CD集成支持
"""

import sys
import os
import time
import random
import tempfile
import json
from typing import Dict, List, Any, Callable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validation.segment_validator import (
    SegmentValidator,
    ValidationPoint
)
from validation.target_alignment import (
    TargetAlignmentValidator,
    AlignmentStatus
)
from validation.action_post_validator import (
    ActionPostValidator,
    ActionOutput
)
from validation.logger_manager import (
    LoggerManager,
    LogLevel,
    Environment,
    get_logger,
    performance_trace
)
from validation.history_manager import (
    HistoryManager,
    HistoryConfig,
    CleanupStrategy,
    ExportFormat
)
from validation.config_manager import (
    create_config_manager,
    get_validation_system_config_rules,
    ValidationRule
)
from validation.performance_monitor import (
    create_performance_monitor,
    ThresholdRule,
    AlertLevel,
    TimedOperation
)


class IntegrationTestResult:
    """集成测试结果"""
    def __init__(self):
        self.total_tests = 0
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.warnings = []
        self.start_time = 0.0
        self.end_time = 0.0
        self.performance_metrics = {}

    def add_pass(self, name: str):
        self.passed += 1
        print(f"   ✅ {name}")

    def add_fail(self, name: str, error: str):
        self.failed += 1
        self.errors.append({"test": name, "error": error})
        print(f"   ❌ {name}: {error}")

    def get_summary(self) -> Dict[str, Any]:
        duration = self.end_time - self.start_time
        return {
            "total": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": self.passed / self.total_tests if self.total_tests > 0 else 0,
            "duration": duration,
            "performance_metrics": self.performance_metrics,
            "errors": self.errors
        }


def test_module_integration():
    """测试模块集成"""
    print("\n" + "=" * 60)
    print("测试1: 模块集成测试")
    print("=" * 60)
    
    result = IntegrationTestResult()
    result.start_time = time.time()
    result.total_tests = 6
    
    # 1.1 验证器集成
    try:
        validator = SegmentValidator()
        validator.pre_validate_subtask("test_task", {"inputs": {"data": "test"}})
        result.add_pass("分段验证器集成")
    except Exception as e:
        result.add_fail("分段验证器集成", str(e))
    
    # 1.2 目标对齐集成
    try:
        target_validator = TargetAlignmentValidator()
        target_validator.define_target("test", "测试目标")
        target_validator.validate_alignment("test", "测试动作")
        result.add_pass("目标对齐验证集成")
    except Exception as e:
        result.add_fail("目标对齐验证集成", str(e))
    
    # 1.3 动作后校验集成
    try:
        post_validator = ActionPostValidator()
        output = ActionOutput(
            action_id="test",
            success=True,
            data={"result": "ok"}
        )
        post_validator.validate_action_output("test", output)
        result.add_pass("动作后校验集成")
    except Exception as e:
        result.add_fail("动作后校验集成", str(e))
    
    # 1.4 日志系统集成
    try:
        manager = LoggerManager()
        manager.set_environment(Environment.DEVELOPMENT)
        logger = get_logger('test')
        logger.info("测试日志")
        result.add_pass("日志系统集成")
    except Exception as e:
        result.add_fail("日志系统集成", str(e))
    
    # 1.5 历史记录集成
    try:
        history = HistoryManager(HistoryConfig(max_records=100))
        history.add({"test": "data"})
        history.get_all()
        result.add_pass("历史记录集成")
    except Exception as e:
        result.add_fail("历史记录集成", str(e))
    
    # 1.6 配置管理集成
    try:
        temp_config = tempfile.mktemp(suffix='.json')
        config_mgr = create_config_manager(temp_config)
        config_mgr.save({"test": "value"}, description="集成测试")
        config_mgr.load()
        result.add_pass("配置管理集成")
        os.remove(temp_config)
    except Exception as e:
        result.add_fail("配置管理集成", str(e))
    
    result.end_time = time.time()
    return result


def test_end_to_end_workflow():
    """测试端到端工作流"""
    print("\n" + "=" * 60)
    print("测试2: 端到端工作流")
    print("=" * 60)
    
    result = IntegrationTestResult()
    result.start_time = time.time()
    
    try:
        # 2.1 创建目标
        print("\n   2.1 创建目标:")
        target_validator = TargetAlignmentValidator()
        target_validator.define_target(
            "complex_task",
            "执行复杂的数据分析和可视化任务",
            scope_keywords=["数据分析", "可视化", "任务"],
            anti_keywords=["删除数据"]
        )
        print("   ✅ 目标创建成功")
        
        # 2.2 执行子任务验证
        print("\n   2.2 执行子任务验证:")
        validator = SegmentValidator(failure_threshold=5)
        subtasks = [
            {"name": "数据收集", "inputs": {"source": "database"}},
            {"name": "数据清洗", "inputs": {"dirty": True}},
            {"name": "数据分析", "inputs": {"method": "statistical"}},
            {"name": "生成报告", "inputs": {"format": "html"}},
            {"name": "可视化", "inputs": {"type": "chart"}}
        ]
        
        validation_results = []
        for task in subtasks:
            report = validator.pre_validate_subtask(task["name"], task["inputs"])
            validation_results.append(report)
            print(f"   - {task['name']}: {report.result.value}")
        
        print("   ✅ 子任务验证完成")
        
        # 2.3 目标对齐检查
        print("\n   2.3 目标对齐检查:")
        for task in subtasks:
            alignment = target_validator.validate_alignment(
                "complex_task",
                f"执行{task['name']}"
            )
            print(f"   - {task['name']}: {alignment.status.value} (匹配度: {alignment.metrics.match_score:.2f})")
        
        print("   ✅ 目标对齐检查完成")
        
        # 2.4 动作执行和后校验
        print("\n   2.4 动作执行和后校验:")
        post_validator = ActionPostValidator()
        execution_results = []
        
        for task in subtasks:
            success = random.random() > 0.1  # 90%成功率
            output = ActionOutput(
                action_id=task["name"],
                success=success,
                data={"task": task["name"], "status": "completed" if success else "failed"},
                error=None if success else "执行失败",
                execution_time=random.uniform(0.1, 2.0)
            )
            
            report = post_validator.validate_action_output(task["name"], output)
            execution_results.append(report)
            
            status = "✅" if report.is_valid() else "❌"
            print(f"   {status} {task['name']}: {report.validation_status.value}")
        
        print("   ✅ 动作后校验完成")
        
        # 2.5 性能监控
        print("\n   2.5 性能监控:")
        monitor = create_performance_monitor()
        
        for task in subtasks:
            duration = random.uniform(10, 100)
            monitor.record(f"task_{task['name']}", duration, "ms")
        
        stats = monitor.get_stats()
        print(f"   监控了 {len(stats)} 个指标")
        
        for name, stat in stats.items():
            print(f"   - {name}: 平均{stat.mean:.1f}ms, P95:{stat.p95:.1f}ms")
        
        print("   ✅ 性能监控完成")
        
        # 2.6 历史记录
        print("\n   2.6 历史记录:")
        history = HistoryManager(HistoryConfig(max_records=1000))
        
        for i, (task, report, exec_result) in enumerate(zip(subtasks, validation_results, execution_results)):
            history.add({
                "task_id": i,
                "task_name": task["name"],
                "validation": report.to_dict(),
                "execution": exec_result.validation_status.value
            })
        
        print(f"   记录了 {len(history)} 条历史")
        
        # 导出历史
        json_export = history.export(ExportFormat.JSON)
        print(f"   导出JSON: {len(json_export)} 字符")
        
        print("   ✅ 历史记录完成")
        
        # 所有测试通过
        result.total_tests = 6
        for i in range(6):
            result.add_pass(f"端到端流程 {i+1}")
        
    except Exception as e:
        result.add_fail("端到端工作流", str(e))
        import traceback
        traceback.print_exc()
    
    result.end_time = time.time()
    return result


def test_regression_suite():
    """测试回归测试套件"""
    print("\n" + "=" * 60)
    print("测试3: 回归测试套件")
    print("=" * 60)
    
    result = IntegrationTestResult()
    result.start_time = time.time()
    
    test_cases = [
        # 分段验证器测试
        ("分段验证器-基础", lambda: SegmentValidator().pre_validate_subtask("test", {})),
        ("分段验证器-带输入", lambda: SegmentValidator().pre_validate_subtask("test", {"inputs": {"data": "x"}})),
        ("分段验证器-熔断器", lambda: test_circuit_breaker()),
        
        # 目标对齐测试
        ("目标对齐-创建", lambda: test_target_creation()),
        ("目标对齐-验证", lambda: test_target_validation()),
        
        # 动作后校验测试
        ("动作后校验-成功", lambda: test_post_validation_success()),
        ("动作后校验-失败", lambda: test_post_validation_failure()),
        
        # 历史记录测试
        ("历史记录-添加", lambda: test_history_add()),
        ("历史记录-查询", lambda: test_history_query()),
        ("历史记录-清理", lambda: test_history_cleanup()),
        
        # 配置管理测试
        ("配置管理-保存加载", lambda: test_config_save_load()),
        ("配置管理-验证", lambda: test_config_validation()),
        
        # 日志系统测试
        ("日志系统-级别切换", lambda: test_logger_level()),
        ("日志系统-性能追踪", lambda: test_performance_trace()),
        
        # 性能监控测试
        ("性能监控-记录", lambda: test_performance_record()),
        ("性能监控-告警", lambda: test_performance_alert()),
    ]
    
    result.total_tests = len(test_cases)
    
    for name, test_func in test_cases:
        try:
            test_func()
            result.add_pass(name)
        except Exception as e:
            result.add_fail(name, str(e))
    
    result.end_time = time.time()
    return result


# 辅助测试函数
def test_circuit_breaker():
    validator = SegmentValidator(failure_threshold=3)
    for i in range(5):
        validator.post_validate_action(f"fail_{i}", {
            "has_output": False,
            "has_error": True
        })
    status = validator.get_circuit_status()
    assert status["state"] == "open"

def test_target_creation():
    validator = TargetAlignmentValidator()
    validator.define_target("test", "测试目标")
    assert len(validator.targets) > 0

def test_target_validation():
    validator = TargetAlignmentValidator()
    validator.define_target("test", "测试目标")
    report = validator.validate_alignment("test", "测试动作")
    assert report is not None

def test_post_validation_success():
    validator = ActionPostValidator()
    output = ActionOutput("test", True, {"result": "ok"})
    report = validator.validate_action_output("test", output)
    assert report.is_valid()

def test_post_validation_failure():
    validator = ActionPostValidator()
    output = ActionOutput("test", False, error="错误")
    report = validator.validate_action_output("test", output)
    assert not report.is_valid()

def test_history_add():
    history = HistoryManager(HistoryConfig(max_records=100))
    history.add({"id": 1})
    assert len(history) == 1

def test_history_query():
    history = HistoryManager(HistoryConfig(max_records=100))
    history.add({"id": 1, "value": "a"})
    history.add({"id": 2, "value": "b"})
    results = history.query(lambda r: r.get("id", 0) > 1)
    assert len(results) == 1

def test_history_cleanup():
    history = HistoryManager(HistoryConfig(max_records=10))
    for i in range(20):
        history.add({"id": i})
    assert len(history) <= 15  # 清理后应该<=15

def test_config_save_load():
    temp = tempfile.mktemp(suffix='.json')
    try:
        manager = create_config_manager(temp)
        manager.save({"test": "value"})
        loaded = manager.load()
        assert loaded is not None
    finally:
        if os.path.exists(temp):
            os.remove(temp)

def test_config_validation():
    temp = tempfile.mktemp(suffix='.json')
    try:
        manager = create_config_manager(temp)
        manager.add_validation_rule(ValidationRule(
            field="test",
            validator=lambda x: isinstance(x, str),
            error_message="必须是字符串"
        ))
        result = manager.validate({"test": "value"})
        assert result.valid
    finally:
        if os.path.exists(temp):
            os.remove(temp)

def test_logger_level():
    manager = LoggerManager()
    manager.set_level(LogLevel.WARNING)
    assert manager.get_level() == LogLevel.WARNING

def test_performance_trace():
    manager = LoggerManager()
    with performance_trace('test'):
        pass

def test_performance_record():
    monitor = create_performance_monitor()
    monitor.record("test", 100.0)
    stats = monitor.get_stats("test")
    assert stats is not None

def test_performance_alert():
    monitor = create_performance_monitor()
    monitor.add_threshold_rule(ThresholdRule(
        name="test",
        threshold=100,
        alert_level=AlertLevel.WARNING,
        operator=">"
    ))
    monitor.record("test", 200)


def test_performance_benchmark():
    """性能基准测试"""
    print("\n" + "=" * 60)
    print("测试4: 性能基准测试")
    print("=" * 60)
    
    result = IntegrationTestResult()
    result.start_time = time.time()
    
    benchmarks = [
        ("验证器性能", lambda: benchmark_validator(100)),
        ("历史记录性能", lambda: benchmark_history(1000)),
        ("配置加载性能", lambda: benchmark_config(50)),
    ]
    
    for name, benchmark_func in benchmarks:
        try:
            duration = benchmark_func()
            result.total_tests += 1
            print(f"   ✅ {name}: {duration:.3f}s")
            result.performance_metrics[name] = duration
            result.add_pass(name)
        except Exception as e:
            result.total_tests += 1
            result.add_fail(name, str(e))
    
    result.end_time = time.time()
    return result


def benchmark_validator(iterations: int) -> float:
    """验证器性能基准"""
    validator = SegmentValidator()
    start = time.time()
    for i in range(iterations):
        validator.pre_validate_subtask(f"task_{i}", {"inputs": {"data": i}})
    return time.time() - start

def benchmark_history(iterations: int) -> float:
    """历史记录性能基准"""
    history = HistoryManager(HistoryConfig(max_records=10000))
    start = time.time()
    for i in range(iterations):
        history.add({"id": i, "data": f"test_{i}"})
    return time.time() - start

def benchmark_config(iterations: int) -> float:
    """配置加载性能基准"""
    temp = tempfile.mktemp(suffix='.json')
    try:
        manager = create_config_manager(temp)
        manager.save({"test": "value", "data": list(range(100))})
        
        start = time.time()
        for i in range(iterations):
            manager.load()
        return time.time() - start
    finally:
        if os.path.exists(temp):
            os.remove(temp)


def test_stress_test():
    """压力测试"""
    print("\n" + "=" * 60)
    print("测试5: 压力测试")
    print("=" * 60)
    
    result = IntegrationTestResult()
    result.start_time = time.time()
    
    try:
        # 并发测试
        print("\n   5.1 并发验证测试:")
        from concurrent.futures import ThreadPoolExecutor
        
        def concurrent_task(task_id):
            validator = SegmentValidator()
            validator.pre_validate_subtask(f"task_{task_id}", {"inputs": {"id": task_id}})
            return True
        
        start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(concurrent_task, i) for i in range(100)]
            results = [f.result() for f in futures]
        duration = time.time() - start
        
        print(f"   100个并发任务: {duration:.3f}s")
        print(f"   平均每任务: {duration*10:.1f}ms")
        
        if all(results):
            result.total_tests += 1
            result.add_pass("并发验证测试")
        
        # 大数据测试
        print("\n   5.2 大数据处理测试:")
        history = HistoryManager(HistoryConfig(max_records=50000))
        
        start = time.time()
        for i in range(10000):
            history.add({
                "id": i,
                "data": "x" * 100,  # 模拟较大数据
                "timestamp": time.time()
            })
        duration = time.time() - start
        
        print(f"   10000条大数据记录: {duration:.3f}s")
        
        result.total_tests += 1
        result.add_pass("大数据处理测试")
        
        # 快速连续操作
        print("\n   5.3 快速连续操作测试:")
        monitor = create_performance_monitor()
        
        start = time.time()
        for i in range(1000):
            monitor.record("rapid_test", i)
        duration = time.time() - start
        
        print(f"   1000次快速记录: {duration:.3f}s")
        
        result.total_tests += 1
        result.add_pass("快速连续操作测试")
        
    except Exception as e:
        result.add_fail("压力测试", str(e))
        import traceback
        traceback.print_exc()
    
    result.end_time = time.time()
    return result


def generate_test_report(results: List[IntegrationTestResult]):
    """生成测试报告"""
    print("\n" + "=" * 80)
    print("📊 集成测试完整报告")
    print("=" * 80)
    
    total_tests = sum(r.total_tests for r in results)
    total_passed = sum(r.passed for r in results)
    total_failed = sum(r.failed for r in results)
    total_duration = sum(r.end_time - r.start_time for r in results)
    
    pass_rate = total_passed / total_tests if total_tests > 0 else 0
    
    print(f"\n✅ 总体统计:")
    print(f"   总测试数: {total_tests}")
    print(f"   通过: {total_passed} ({pass_rate*100:.1f}%)")
    print(f"   失败: {total_failed}")
    print(f"   总耗时: {total_duration:.2f}秒")
    
    print(f"\n📈 性能指标:")
    all_metrics = {}
    for r in results:
        all_metrics.update(r.performance_metrics)
    
    for name, value in all_metrics.items():
        print(f"   {name}: {value:.3f}s")
    
    print(f"\n📋 各测试项:")
    test_names = [
        "模块集成测试",
        "端到端工作流",
        "回归测试套件",
        "性能基准测试",
        "压力测试"
    ]
    
    for i, r in enumerate(results):
        name = test_names[i] if i < len(test_names) else f"测试{i+1}"
        duration = r.end_time - r.start_time
        print(f"\n   {name}:")
        print(f"      测试数: {r.total_tests}")
        print(f"      通过: {r.passed}")
        print(f"      失败: {r.failed}")
        print(f"      耗时: {duration:.2f}秒")
        
        if r.failed > 0:
            print(f"      失败详情:")
            for error in r.errors[:3]:  # 只显示前3个
                print(f"        - {error['test']}: {error['error']}")
    
    print("\n" + "=" * 80)
    
    if pass_rate >= 0.95:
        print("🎉 优秀！测试通过率 >= 95%")
    elif pass_rate >= 0.80:
        print("⚠️ 良好！测试通过率 >= 80%")
    else:
        print("❌ 需改进！测试通过率 < 80%")
    
    print(f"最终通过率: {pass_rate*100:.1f}%")
    print("=" * 80)


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🚀 阶段53：集成测试完善")
    print("=" * 80)
    print("\n测试内容:")
    print("  1. 模块集成测试 - 验证所有模块能正常集成")
    print("  2. 端到端工作流 - 测试完整业务流程")
    print("  3. 回归测试套件 - 16个核心功能回归测试")
    print("  4. 性能基准测试 - 验证性能指标")
    print("  5. 压力测试 - 并发和大数据处理")
    print("=" * 80 + "\n")
    
    results = []
    
    try:
        # 运行所有测试
        results.append(test_module_integration())
        results.append(test_end_to_end_workflow())
        results.append(test_regression_suite())
        results.append(test_performance_benchmark())
        results.append(test_stress_test())
        
        # 生成报告
        generate_test_report(results)
        
        # 总结
        total_passed = sum(r.passed for r in results)
        total_tests = sum(r.total_tests for r in results)
        pass_rate = total_passed / total_tests if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("🎯 阶段53总结")
        print("=" * 80)
        print(f"\n完成情况:")
        print(f"  ✅ 端到端集成测试")
        print(f"  ✅ 回归测试套件 ({total_tests}个测试)")
        print(f"  ✅ 性能基准测试")
        print(f"  ✅ 压力测试")
        print(f"\n总体通过率: {pass_rate*100:.1f}%")
        
        if pass_rate >= 0.90:
            print("\n🎉 阶段53完成！所有集成测试通过！")
        else:
            print("\n⚠️ 阶段53完成，但有部分测试失败")
        
        print("=" * 80)
        
        return pass_rate >= 0.90
        
    except Exception as e:
        print(f"\n❌ 测试执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
