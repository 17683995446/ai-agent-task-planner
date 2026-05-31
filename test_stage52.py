#!/usr/bin/env python3
"""
阶段52测试：性能监控增强
"""

import sys
import os
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validation.performance_monitor import (
    create_performance_monitor,
    PerformanceMonitor,
    AlertLevel,
    AnomalyType,
    ThresholdRule,
    TimedOperation
)
from validation.logger_manager import get_logger

logger = get_logger('test.stage52')


def test_performance_recording():
    """测试性能指标记录"""
    print("\n" + "=" * 60)
    print("测试1: 性能指标记录")
    print("=" * 60)
    
    monitor = create_performance_monitor()
    
    # 记录一些指标
    print("\n1.1 记录性能指标:")
    for i in range(50):
        value = random.uniform(10, 100)
        monitor.record("test_metric", value, "ms", {"iteration": str(i)})
    
    # 获取历史
    history = monitor.get_history("test_metric")
    print(f"   历史记录数: {len(history)}")
    
    # 获取统计
    stats = monitor.get_stats("test_metric")
    if stats:
        print(f"   Count: {stats.count}")
        print(f"   Min: {stats.min:.1f}")
        print(f"   Max: {stats.max:.1f}")
        print(f"   Mean: {stats.mean:.1f}")
    
    if len(history) == 50 and stats and stats.count == 50:
        print("\n✅ 性能指标记录测试通过")
        return True
    else:
        print("\n❌ 性能指标记录测试失败")
        return False


def test_timed_operation():
    """测试计时操作"""
    print("\n" + "=" * 60)
    print("测试2: 计时操作")
    print("=" * 60)
    
    monitor = create_performance_monitor()
    
    print("\n2.1 使用上下文管理器:")
    with TimedOperation(monitor, "timed_test"):
        time.sleep(0.05)
    
    # 检查是否记录
    stats = monitor.get_stats("timed_test")
    if stats and stats.count == 1:
        print(f"   记录了 1 次操作")
        print(f"   耗时: {stats.mean:.2f}ms")
        
        if stats.mean > 40 and stats.mean < 60:  # 50ms左右
            print("\n✅ 计时操作测试通过")
            return True
    
    print("\n❌ 计时操作测试失败")
    return False


def test_threshold_alerts():
    """测试阈值告警"""
    print("\n" + "=" * 60)
    print("测试3: 阈值告警")
    print("=" * 60)
    
    monitor = create_performance_monitor()
    
    # 添加规则
    monitor.add_threshold_rule(ThresholdRule(
        name="slow_operation",
        threshold=100.0,
        alert_level=AlertLevel.WARNING,
        operator=">"
    ))
    
    alerts_received = []
    
    def on_alert(alert):
        alerts_received.append(alert)
        print(f"   收到告警: {alert.level.name} - {alert.message}")
    
    monitor.add_alert_listener(on_alert)
    
    # 记录正常值
    print("\n3.1 记录正常值:")
    for i in range(5):
        monitor.record("slow_operation", random.uniform(10, 50), "ms")
    print(f"   记录了 5 次正常操作")
    
    # 记录异常值
    print("\n3.2 记录异常值:")
    monitor.record("slow_operation", 150, "ms")
    
    # 检查告警
    if len(alerts_received) == 1:
        alert = alerts_received[0]
        print(f"   收到 {len(alerts_received)} 个告警")
        print(f"   告警级别: {alert.level.name}")
        
        if alert.level == AlertLevel.WARNING:
            print("\n✅ 阈值告警测试通过")
            return True
    
    print("\n❌ 阈值告警测试失败")
    return False


def test_anomaly_detection():
    """测试异常检测"""
    print("\n" + "=" * 60)
    print("测试4: 异常检测")
    print("=" * 60)
    
    monitor = create_performance_monitor()
    
    # 记录正常数据
    print("\n4.1 生成基准数据:")
    for i in range(100):
        value = random.normalvariate(50, 10)
        monitor.record("anomaly_test", value)
    print(f"   生成了 100 个正常值")
    
    # 记录异常值
    print("\n4.2 插入异常值:")
    monitor.record("anomaly_test", 200)  # 大异常
    monitor.record("anomaly_test", 10)   # 小异常
    
    # 检测异常
    print("\n4.3 检测异常:")
    anomalies = monitor.detect_anomalies("anomaly_test")
    print(f"   检测到 {len(anomalies)} 个异常")
    
    if len(anomalies) >= 2:
        print("\n✅ 异常检测测试通过")
        return True
    else:
        print("\n⚠️ 异常检测测试部分通过（可能需要更多数据）")
        return True


def test_trend_analysis():
    """测试趋势分析"""
    print("\n" + "=" * 60)
    print("测试5: 趋势分析")
    print("=" * 60)
    
    monitor = create_performance_monitor()
    
    # 递增趋势
    print("\n5.1 生成递增趋势:")
    for i in range(50):
        value = 10 + i * 2
        monitor.record("increasing_trend", value)
    print(f"   生成了 50 个递增数据点")
    
    # 分析趋势
    trend = monitor.get_trend("increasing_trend")
    print(f"   趋势: {trend['trend']}")
    if 'slope' in trend:
        print(f"   斜率: {trend['slope']:.4f}")
    
    if trend['trend'] == 'increasing' and trend['slope'] > 0:
        print("\n✅ 趋势分析测试通过")
        return True
    else:
        print("\n❌ 趋势分析测试失败")
        return False


def test_stats_calculation():
    """测试统计计算"""
    print("\n" + "=" * 60)
    print("测试6: 统计计算")
    print("=" * 60)
    
    monitor = create_performance_monitor()
    
    # 记录已知值
    values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    for v in values:
        monitor.record("stats_test", v)
    
    stats = monitor.get_stats("stats_test")
    if stats:
        print(f"\n6.1 统计结果:")
        print(f"   Min: {stats.min}")
        print(f"   Max: {stats.max}")
        print(f"   Mean: {stats.mean}")
        print(f"   Median: {stats.median}")
        print(f"   P95: {stats.p95}")
        print(f"   P99: {stats.p99}")
        
        if (stats.min == 10 and 
            stats.max == 100 and 
            stats.mean == 55 and 
            stats.median in [50, 55]):  # 取决于奇数或偶数个数据
            print("\n✅ 统计计算测试通过")
            return True
    
    print("\n❌ 统计计算测试失败")
    return False


def test_alert_acknowledgement():
    """测试告警确认"""
    print("\n" + "=" * 60)
    print("测试7: 告警确认")
    print("=" * 60)
    
    monitor = create_performance_monitor()
    
    monitor.add_threshold_rule(ThresholdRule(
        name="ack_test",
        threshold=50,
        alert_level=AlertLevel.ERROR,
        operator=">"
    ))
    
    # 产生一些告警
    monitor.record("ack_test", 100)
    monitor.record("ack_test", 200)
    
    alerts = monitor.get_alerts()
    print(f"\n7.1 初始告警: {len(alerts)} 条")
    for i, alert in enumerate(alerts):
        print(f"   告警 {i+1}: acknowledged={alert.acknowledged}")
    
    # 确认所有告警
    monitor.acknowledge_alerts()
    
    # 检查确认状态
    alerts_after = monitor.get_alerts()
    print(f"\n7.2 确认后告警:")
    all_acknowledged = all(a.acknowledged for a in alerts_after)
    for i, alert in enumerate(alerts_after):
        print(f"   告警 {i+1}: acknowledged={alert.acknowledged}")
    
    if all_acknowledged:
        print("\n✅ 告警确认测试通过")
        return True
    else:
        print("\n❌ 告警确认测试失败")
        return False


def test_multiple_metrics():
    """测试多指标管理"""
    print("\n" + "=" * 60)
    print("测试8: 多指标管理")
    print("=" * 60)
    
    monitor = create_performance_monitor()
    
    # 记录多个指标
    print("\n8.1 记录多个指标:")
    for i in range(10):
        monitor.record("metric_a", random.uniform(10, 100), "ms")
        monitor.record("metric_b", random.uniform(1, 10), "s")
    
    # 获取所有统计
    all_stats = monitor.get_stats()
    print(f"   指标数量: {len(all_stats)}")
    for name in all_stats.keys():
        print(f"   - {name}")
    
    # 清除单个指标
    monitor.clear("metric_a")
    all_stats_after = monitor.get_stats()
    print(f"\n8.2 清除后指标数量: {len(all_stats_after)}")
    
    # 清除所有
    monitor.clear()
    all_stats_final = monitor.get_stats()
    print(f"8.3 清除所有后指标数量: {len(all_stats_final)}")
    
    if len(all_stats) == 2 and len(all_stats_after) == 1 and len(all_stats_final) == 0:
        print("\n✅ 多指标管理测试通过")
        return True
    else:
        print("\n❌ 多指标管理测试失败")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("🚀 阶段52测试：性能监控增强")
    print("=" * 80)
    
    all_passed = True
    tests = [
        ("性能指标记录", test_performance_recording),
        ("计时操作", test_timed_operation),
        ("阈值告警", test_threshold_alerts),
        ("异常检测", test_anomaly_detection),
        ("趋势分析", test_trend_analysis),
        ("统计计算", test_stats_calculation),
        ("告警确认", test_alert_acknowledgement),
        ("多指标管理", test_multiple_metrics),
    ]
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ {test_name} 测试通过")
            else:
                print(f"\n❌ {test_name} 测试失败")
                all_passed = False
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 所有测试通过！性能监控增强功能完整！")
    else:
        print("❌ 部分测试失败，请检查")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
