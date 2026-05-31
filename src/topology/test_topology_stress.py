"""
拓扑压力测试运行脚本
基于第一性原理的AI Agent任务规划系统
"""

import sys
import os

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from topology_stress_tester import (
    TopologyStressTester, 
    run_topology_stress_tests, 
    run_tests_and_get_report
)


def run_stress_test_suite():
    """运行压力测试套件"""
    print("=" * 80)
    print("拓扑依赖拆解层 - 压力测试套件")
    print("=" * 80)
    
    # 运行所有测试
    print("\n正在运行压力测试...")
    tester = TopologyStressTester()
    report = tester.run_all_tests()
    
    # 打印报告
    print("\n" + "=" * 80)
    print("压力测试报告")
    print("=" * 80)
    print(f"\n总测试数: {report.total_tests}")
    print(f"成功测试数: {report.successful_tests}")
    print(f"失败测试数: {report.total_tests - report.successful_tests}")
    print(f"总执行时间: {report.total_execution_time:.2f}秒")
    print(f"最大节点数: {report.max_nodes}")
    print(f"最大边数: {report.max_edges}")
    print(f"稳定性评分: {report.stability_score:.1f}%")
    
    # 打印详细结果
    print("\n" + "=" * 80)
    print("详细测试结果")
    print("=" * 80)
    for i, result in enumerate(report.test_results, 1):
        status = "✅ 通过" if result.is_successful else "❌ 失败"
        print(f"\n测试 {i}: {result.test_name} ({result.test_category.value})")
        print(f"  状态: {status}")
        print(f"  执行时间: {result.execution_time:.3f}秒")
        print(f"  节点数: {result.node_count}")
        print(f"  边数: {result.edge_count}")
        
        if result.issues_found:
            print(f"  发现的问题:")
            for issue in result.issues_found:
                print(f"    - {issue}")
        
        if result.details:
            print(f"  详细信息:")
            for key, value in result.details.items():
                print(f"    - {key}: {value}")
    
    # 打印建议
    print("\n" + "=" * 80)
    print("优化建议")
    print("=" * 80)
    for i, recommendation in enumerate(report.recommendations, 1):
        print(f"\n建议 {i}: {recommendation}")
    
    # 总结
    print("\n" + "=" * 80)
    if report.stability_score >= 90:
        print("🎯 优秀！拓扑层稳定性表现极佳。")
    elif report.stability_score >= 70:
        print("👍 良好！拓扑层表现稳定，有少量优化空间。")
    elif report.stability_score >= 50:
        print("⚠️ 一般！建议检查失败的测试用例。")
    else:
        print("❌ 需要关注！请修复失败的测试用例。")
    print("=" * 80)
    
    return report


if __name__ == "__main__":
    report = run_stress_test_suite()
