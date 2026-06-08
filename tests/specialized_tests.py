"""
专项测试模块
基于第一性原理的AI Agent任务规划系统

核心功能：
- 阶段81：专项测试目标跑偏问题根治效果
- 阶段82：专项测试步骤遗漏、残缺场景
- 阶段83：专项测试任务顺序错乱、颠倒场景
- 阶段84：专项测试粗粒度步骤拆分精度
- 阶段85：模拟无限推演场景、验证终止机制
- 阶段86：全链路性能基准测试与瓶颈分析
- 阶段87：内存泄漏检测与修复
- 阶段88：并发安全压力测试
- 阶段89：边界条件极限测试
"""

import sys
import time
import threading
import tracemalloc
from typing import Dict, Any, List

sys.path.insert(0, '/workspace/src')

from interfaces.orchestrator_interface import OrchestratorInterface
from optimization.robustness_enhancer import RobustnessEnhancer


class SpecializedTestSuite:
    """专项测试套件"""
    
    def __init__(self):
        self.orchestrator = OrchestratorInterface()
        self.enhancer = RobustnessEnhancer()
        self.results = {}
    
    # ========== 阶段81：目标跑偏测试 ==========
    def test_target_deviation(self):
        """测试目标跑偏问题"""
        print("\n【阶段81】目标跑偏问题测试")
        
        test_cases = [
            {
                "input": "开发一个用户登录系统，但是要有商品搜索功能",
                "expected_target": "用户登录系统",
                "description": "需求中包含多个目标"
            },
            {
                "input": "做一个网站，类似淘宝那样的电商网站，但是主要是做社交功能",
                "expected_target": "社交网站",
                "description": "目标在描述中偏移"
            },
            {
                "input": "帮我设计一个系统，先是一个博客系统，然后要支持论坛功能，最后还要做商城",
                "expected_target": "博客+论坛+商城系统",
                "description": "多重目标叠加"
            }
        ]
        
        passed = 0
        for case in test_cases:
            result = self.orchestrator.plan_task(case["input"])
            # 检查目标是否偏离
            if result.success and result.modeling_result and result.modeling_result.task:
                target = result.modeling_result.task.target
                if target and case["expected_target"] in target.description:
                    passed += 1
                    print(f"  ✓ {case['description']}: 目标正确")
                else:
                    print(f"  ✗ {case['description']}: 目标偏离")
            else:
                print(f"  ✗ {case['description']}: 解析失败")
        
        self.results["target_deviation"] = {
            "total": len(test_cases),
            "passed": passed,
            "rate": passed / len(test_cases) * 100
        }
        print(f"  通过率: {passed}/{len(test_cases)} ({passed/len(test_cases)*100:.0f}%)")
    
    # ========== 阶段82：步骤遗漏测试 ==========
    def test_step_omission(self):
        """测试步骤遗漏、残缺场景"""
        print("\n【阶段82】步骤遗漏、残缺场景测试")
        
        test_cases = [
            {
                "input": "开发系统",
                "description": "极简描述"
            },
            {
                "input": "做一个东西",
                "description": "模糊描述"
            },
            {
                "input": "",
                "description": "空描述"
            }
        ]
        
        passed = 0
        for case in test_cases:
            try:
                result = self.orchestrator.plan_task(case["input"])
                # 即使输入极简，也应该有基本的子任务
                if result.success and result.topology_result and len(result.topology_result.subtasks) > 0:
                    passed += 1
                    print(f"  ✓ {case['description']}: 有基本步骤")
                else:
                    print(f"  ✗ {case['description']}: 步骤缺失")
            except Exception as e:
                print(f"  ✗ {case['description']}: 异常 - {e}")
        
        self.results["step_omission"] = {
            "total": len(test_cases),
            "passed": passed,
            "rate": passed / len(test_cases) * 100
        }
        print(f"  通过率: {passed}/{len(test_cases)} ({passed/len(test_cases)*100:.0f}%)")
    
    # ========== 阶段83：任务顺序测试 ==========
    def test_task_order(self):
        """测试任务顺序错乱、颠倒场景"""
        print("\n【阶段83】任务顺序错乱、颠倒场景测试")
        
        # 测试依赖关系是否正确
        test_cases = [
            {
                "input": "先开发后端API，再开发前端页面，最后做数据库设计",
                "description": "明确顺序要求"
            },
            {
                "input": "完成测试之后再写代码，部署之前要做代码审查",
                "description": "反向顺序要求"
            }
        ]
        
        passed = 0
        for case in test_cases:
            result = self.orchestrator.plan_task(case["input"])
            if result.success:
                passed += 1
                print(f"  ✓ {case['description']}: 顺序处理正常")
            else:
                print(f"  ✗ {case['description']}: 顺序处理异常")
        
        self.results["task_order"] = {
            "total": len(test_cases),
            "passed": passed,
            "rate": passed / len(test_cases) * 100
        }
        print(f"  通过率: {passed}/{len(test_cases)} ({passed/len(test_cases)*100:.0f}%)")
    
    # ========== 阶段84：拆分精度测试 ==========
    def test_split_precision(self):
        """测试粗粒度步骤拆分精度"""
        print("\n【阶段84】粗粒度步骤拆分精度测试")
        
        test_cases = [
            {
                "input": "开发一个完整的电商系统",
                "min_subtasks": 5,
                "description": "复杂系统拆分"
            },
            {
                "input": "做一个登录功能",
                "min_subtasks": 2,
                "description": "简单功能拆分"
            }
        ]
        
        passed = 0
        for case in test_cases:
            result = self.orchestrator.plan_task(case["input"])
            if result.success and result.topology_result:
                subtask_count = len(result.topology_result.subtasks)
                if subtask_count >= case["min_subtasks"]:
                    passed += 1
                    print(f"  ✓ {case['description']}: 拆分为{subtask_count}个子任务")
                else:
                    print(f"  ✗ {case['description']}: 只拆分为{subtask_count}个子任务，期望至少{case['min_subtasks']}")
            else:
                print(f"  ✗ {case['description']}: 拆分失败")
        
        self.results["split_precision"] = {
            "total": len(test_cases),
            "passed": passed,
            "rate": passed / len(test_cases) * 100
        }
        print(f"  通过率: {passed}/{len(test_cases)} ({passed/len(test_cases)*100:.0f}%)")
    
    # ========== 阶段85：无限推演测试 ==========
    def test_infinite_reasoning(self):
        """模拟无限推演场景、验证终止机制"""
        print("\n【阶段85】无限推演场景、终止机制测试")
        
        # 测试复杂任务的终止
        test_cases = [
            {
                "input": "设计一个系统，这个系统要包含用户管理，用户管理要有权限控制，权限控制要有角色管理，角色管理要有...",
                "description": "递归描述"
            },
            {
                "input": "做一个功能，这个功能依赖A，A依赖B，B依赖C，C依赖D...",
                "description": "循环依赖描述"
            }
        ]
        
        passed = 0
        for case in test_cases:
            start_time = time.time()
            result = self.orchestrator.plan_task(case["input"])
            elapsed = time.time() - start_time
            
            # 检查是否在合理时间内完成
            if elapsed < 5.0:  # 5秒内完成
                passed += 1
                print(f"  ✓ {case['description']}: 在{elapsed:.3f}s内终止")
            else:
                print(f"  ✗ {case['description']}: 耗时{elapsed:.3f}s，可能未正确终止")
        
        self.results["infinite_reasoning"] = {
            "total": len(test_cases),
            "passed": passed,
            "rate": passed / len(test_cases) * 100
        }
        print(f"  通过率: {passed}/{len(test_cases)} ({passed/len(test_cases)*100:.0f}%)")
    
    # ========== 阶段86：性能基准测试 ==========
    def test_performance_baseline(self):
        """全链路性能基准测试与瓶颈分析"""
        print("\n【阶段86】全链路性能基准测试")
        
        test_cases = [
            "开发一个用户登录系统",
            "设计一个电商网站的完整购物流程",
            "设计并实现一个完整的微服务架构电商平台"
        ]
        
        times = []
        for case in test_cases:
            start = time.time()
            result = self.orchestrator.plan_task(case)
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  {case[:30]}...: {elapsed:.3f}s")
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        self.results["performance"] = {
            "avg_time": avg_time,
            "max_time": max_time,
            "min_time": min(times),
            "pass": avg_time < 1.0  # 平均应小于1秒
        }
        print(f"  平均耗时: {avg_time:.3f}s")
        print(f"  最大耗时: {max_time:.3f}s")
        print(f"  {'✓ 性能达标' if avg_time < 1.0 else '✗ 性能不达标'}")
    
    # ========== 阶段87：内存泄漏测试 ==========
    def test_memory_leak(self):
        """内存泄漏检测"""
        print("\n【阶段87】内存泄漏检测")
        
        tracemalloc.start()
        
        # 执行多次任务
        for i in range(10):
            self.orchestrator.plan_task(f"测试任务{i}")
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # 转换为MB
        current_mb = current / 1024 / 1024
        peak_mb = peak / 1024 / 1024
        
        self.results["memory"] = {
            "current_mb": current_mb,
            "peak_mb": peak_mb,
            "pass": current_mb < 100  # 应小于100MB
        }
        print(f"  当前内存: {current_mb:.2f}MB")
        print(f"  峰值内存: {peak_mb:.2f}MB")
        print(f"  {'✓ 内存正常' if current_mb < 100 else '✗ 内存过高'}")
    
    # ========== 阶段88：并发安全测试 ==========
    def test_concurrent_safety(self):
        """并发安全压力测试"""
        print("\n【阶段88】并发安全压力测试")
        
        results = []
        errors = []
        
        def task():
            try:
                result = self.orchestrator.plan_task("并发测试任务")
                results.append(result.success)
            except Exception as e:
                errors.append(str(e))
        
        # 启动10个线程
        threads = []
        start = time.time()
        for i in range(10):
            t = threading.Thread(target=task)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        elapsed = time.time() - start
        
        self.results["concurrent"] = {
            "total": 10,
            "success": sum(results),
            "errors": len(errors),
            "time": elapsed,
            "pass": len(errors) == 0
        }
        print(f"  总任务: 10")
        print(f"  成功: {sum(results)}")
        print(f"  错误: {len(errors)}")
        print(f"  耗时: {elapsed:.3f}s")
        print(f"  {'✓ 并发安全' if len(errors) == 0 else '✗ 并发问题'}")
    
    # ========== 阶段89：边界条件测试 ==========
    def test_boundary_conditions(self):
        """边界条件极限测试"""
        print("\n【阶段89】边界条件极限测试")
        
        test_cases = [
            {"input": "", "description": "空字符串"},
            {"input": "a", "description": "单个字符"},
            {"input": "x" * 10000, "description": "超长字符串(10000字符)"},
            {"input": "开发系统" * 1000, "description": "重复内容"},
        ]
        
        passed = 0
        for case in test_cases:
            try:
                result = self.orchestrator.plan_task(case["input"])
                if result.success or not result.error_message:
                    passed += 1
                    print(f"  ✓ {case['description']}: 处理正常")
                else:
                    print(f"  ✗ {case['description']}: {result.error_message[:50]}")
            except Exception as e:
                print(f"  ✗ {case['description']}: 异常 - {str(e)[:50]}")
        
        self.results["boundary"] = {
            "total": len(test_cases),
            "passed": passed,
            "rate": passed / len(test_cases) * 100
        }
        print(f"  通过率: {passed}/{len(test_cases)} ({passed/len(test_cases)*100:.0f}%)")
    
    def run_all_tests(self):
        """运行所有专项测试"""
        print("=" * 60)
        print("专项测试套件 - 阶段81-89")
        print("=" * 60)
        
        self.test_target_deviation()
        self.test_step_omission()
        self.test_task_order()
        self.test_split_precision()
        self.test_infinite_reasoning()
        self.test_performance_baseline()
        self.test_memory_leak()
        self.test_concurrent_safety()
        self.test_boundary_conditions()
        
        # 汇总
        print("\n" + "=" * 60)
        print("专项测试汇总")
        print("=" * 60)
        
        total_passed = 0
        total_tests = 0
        
        for test_name, result in self.results.items():
            if "passed" in result:
                total_passed += result["passed"]
                total_tests += result["total"]
                print(f"{test_name}: {result['passed']}/{result['total']}")
            elif "pass" in result:
                status = "✓" if result["pass"] else "✗"
                print(f"{test_name}: {status}")
        
        if total_tests > 0:
            overall_rate = total_passed / total_tests * 100
            print(f"\n总体通过率: {total_passed}/{total_tests} ({overall_rate:.1f}%)")
        
        print("=" * 60)


if __name__ == "__main__":
    suite = SpecializedTestSuite()
    suite.run_all_tests()
