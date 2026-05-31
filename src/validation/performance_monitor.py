"""
第四层：分段校验收敛层 - 性能监控增强
基于第一性原理的AI Agent任务规划系统

核心功能：
- 性能指标采集
- 异常检测
- 告警系统
- 性能趋势分析
"""

import time
import threading
import statistics
import math
import random
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from validation.logger_manager import get_logger

logger = get_logger('validation.performance')


class AlertLevel(Enum):
    """告警级别"""
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class AnomalyType(Enum):
    """异常类型"""
    SLOW = "slow"  # 慢操作
    ERROR_RATE = "error_rate"  # 错误率过高
    THROUGHPUT = "throughput"  # 吞吐量异常
    RESOURCE = "resource"  # 资源使用异常


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    timestamp: float = field(default_factory=time.time)
    value: float = 0.0
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """告警"""
    level: AlertLevel
    type: AnomalyType
    message: str
    metric: Optional[PerformanceMetric] = None
    threshold: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.name,
            "type": self.type.value,
            "message": self.message,
            "metric": {
                "name": self.metric.name,
                "value": self.metric.value
            } if self.metric else None,
            "threshold": self.threshold,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged
        }


@dataclass
class ThresholdRule:
    """阈值规则"""
    name: str
    threshold: float
    alert_level: AlertLevel
    operator: str = ">"  # ">", "<", ">=", "<=", "=="
    window_size: int = 10  # 窗口大小


@dataclass
class PerformanceStats:
    """性能统计"""
    name: str
    count: int = 0
    min: float = 0.0
    max: float = 0.0
    mean: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    sum: float = 0.0
    last_update: float = field(default_factory=time.time)


class PerformanceMonitor:
    """
    性能监控器
    
    功能：
    - 性能指标采集
    - 异常检测
    - 告警系统
    - 性能趋势分析
    """
    
    def __init__(self, history_size: int = 1000, alert_enabled: bool = True):
        """
        初始化性能监控器
        
        Args:
            history_size: 历史记录大小
            alert_enabled: 是否启用告警
        """
        self.history_size = history_size
        self.alert_enabled = alert_enabled
        
        # 指标存储
        self.metrics: Dict[str, deque] = {}
        
        # 统计数据
        self.stats: Dict[str, PerformanceStats] = {}
        
        # 阈值规则
        self.threshold_rules: List[ThresholdRule] = []
        
        # 告警记录
        self.alerts: deque = deque(maxlen=1000)
        
        # 告警监听器
        self.alert_listeners: List[Callable[[Alert], None]] = []
        
        # 锁
        self._lock = threading.RLock()
        
        logger.info(f"✅ 性能监控器初始化完成 (history_size={history_size})")
    
    def record(self, name: str, value: float, unit: str = "", tags: Optional[Dict[str, str]] = None, metadata: Optional[Dict[str, Any]] = None) -> PerformanceMetric:
        """
        记录性能指标
        
        Args:
            name: 指标名称
            value: 指标值
            unit: 单位
            tags: 标签
            metadata: 元数据
        
        Returns:
            PerformanceMetric: 性能指标
        """
        with self._lock:
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit=unit,
                tags=tags or {},
                metadata=metadata or {}
            )
            
            # 存储指标
            if name not in self.metrics:
                self.metrics[name] = deque(maxlen=self.history_size)
            self.metrics[name].append(metric)
            
            # 更新统计
            self._update_stats(name)
            
            # 检查告警
            if self.alert_enabled:
                self._check_thresholds(metric)
            
            return metric
    
    def _update_stats(self, name: str):
        """更新统计数据"""
        if name not in self.metrics or len(self.metrics[name]) == 0:
            return
        
        values = [m.value for m in self.metrics[name]]
        
        if len(values) == 1:
            self.stats[name] = PerformanceStats(
                name=name,
                count=1,
                min=values[0],
                max=values[0],
                mean=values[0],
                median=values[0],
                std_dev=0.0,
                p95=values[0],
                p99=values[0],
                sum=values[0]
            )
            return
        
        # 排序
        sorted_values = sorted(values)
        
        self.stats[name] = PerformanceStats(
            name=name,
            count=len(values),
            min=min(values),
            max=max(values),
            mean=statistics.mean(values),
            median=statistics.median(values),
            std_dev=statistics.stdev(values) if len(values) >= 2 else 0.0,
            p95=sorted_values[int(len(sorted_values) * 0.95)],
            p99=sorted_values[int(len(sorted_values) * 0.99)],
            sum=sum(values)
        )
    
    def add_threshold_rule(self, rule: ThresholdRule):
        """添加阈值规则"""
        with self._lock:
            self.threshold_rules.append(rule)
            logger.debug(f"添加阈值规则: {rule.name}")
    
    def _check_thresholds(self, metric: PerformanceMetric):
        """检查阈值"""
        for rule in self.threshold_rules:
            if rule.name != metric.name:
                continue
            
            triggered = False
            if rule.operator == ">":
                triggered = metric.value > rule.threshold
            elif rule.operator == "<":
                triggered = metric.value < rule.threshold
            elif rule.operator == ">=":
                triggered = metric.value >= rule.threshold
            elif rule.operator == "<=":
                triggered = metric.value <= rule.threshold
            elif rule.operator == "==":
                triggered = metric.value == rule.threshold
            
            if triggered:
                alert = Alert(
                    level=rule.alert_level,
                    type=AnomalyType.SLOW,
                    message=f"{rule.name}: {metric.value} {metric.unit} {rule.operator} {rule.threshold}",
                    metric=metric,
                    threshold=rule.threshold
                )
                self._send_alert(alert)
    
    def _send_alert(self, alert: Alert):
        """发送告警"""
        with self._lock:
            self.alerts.append(alert)
            
            log_func = {
                AlertLevel.INFO: logger.info,
                AlertLevel.WARNING: logger.warning,
                AlertLevel.ERROR: logger.error,
                AlertLevel.CRITICAL: logger.critical
            }.get(alert.level, logger.warning)
            
            log_func(f"🚨 {alert.level.name}: {alert.message}")
            
            # 通知监听器
            for listener in self.alert_listeners:
                try:
                    listener(alert)
                except Exception as e:
                    logger.error(f"告警监听器执行失败: {e}")
    
    def add_alert_listener(self, listener: Callable[[Alert], None]):
        """添加告警监听器"""
        with self._lock:
            self.alert_listeners.append(listener)
    
    def remove_alert_listener(self, listener: Callable[[Alert], None]):
        """移除告警监听器"""
        with self._lock:
            if listener in self.alert_listeners:
                self.alert_listeners.remove(listener)
    
    def get_stats(self, name: Optional[str] = None) -> Union[Optional[PerformanceStats], Dict[str, PerformanceStats]]:
        """
        获取统计数据
        
        Args:
            name: 指标名称，None则返回所有
        
        Returns:
            统计数据
        """
        with self._lock:
            if name:
                return self.stats.get(name)
            return dict(self.stats)
    
    def get_history(self, name: str, limit: Optional[int] = None) -> List[PerformanceMetric]:
        """
        获取历史数据
        
        Args:
            name: 指标名称
            limit: 返回数量限制
        
        Returns:
            历史数据
        """
        with self._lock:
            if name not in self.metrics:
                return []
            history = list(self.metrics[name])
            if limit and limit < len(history):
                return history[-limit:]
            return history
    
    def get_alerts(self, level: Optional[AlertLevel] = None, limit: Optional[int] = None) -> List[Alert]:
        """
        获取告警记录
        
        Args:
            level: 告警级别过滤
            limit: 返回数量限制
        
        Returns:
            告警记录
        """
        with self._lock:
            alerts = list(self.alerts)
            if level:
                alerts = [a for a in alerts if a.level == level]
            if limit and limit < len(alerts):
                alerts = alerts[-limit:]
            return alerts
    
    def acknowledge_alerts(self, indices: Optional[List[int]] = None):
        """确认告警"""
        with self._lock:
            if indices:
                for i in indices:
                    if 0 <= i < len(self.alerts):
                        self.alerts[i].acknowledged = True
            else:
                for alert in self.alerts:
                    alert.acknowledged = True
    
    def detect_anomalies(self, name: str, method: str = "std_dev", std_dev_threshold: float = 3.0) -> List[PerformanceMetric]:
        """
        检测异常
        
        Args:
            name: 指标名称
            method: 检测方法
            std_dev_threshold: 标准差阈值
        
        Returns:
            异常指标列表
        """
        with self._lock:
            if name not in self.metrics or len(self.metrics[name]) < 10:
                return []
            
            stats = self.stats[name]
            if not stats:
                return []
            
            anomalies = []
            
            for metric in self.metrics[name]:
                if method == "std_dev":
                    z_score = abs(metric.value - stats.mean) / stats.std_dev if stats.std_dev > 0 else 0
                    if z_score > std_dev_threshold:
                        anomalies.append(metric)
                elif method == "percentile":
                    if metric.value > stats.p99 or metric.value < stats.min * 0.5:
                        anomalies.append(metric)
            
            return anomalies
    
    def get_trend(self, name: str, window_size: int = 100) -> Dict[str, Any]:
        """
        获取趋势分析
        
        Args:
            name: 指标名称
            window_size: 窗口大小
        
        Returns:
            趋势分析结果
        """
        with self._lock:
            if name not in self.metrics or len(self.metrics[name]) < 2:
                return {"trend": "insufficient_data"}
            
            history = list(self.metrics[name])[-window_size:]
            if len(history) < 2:
                return {"trend": "insufficient_data"}
            
            # 简单线性回归
            values = [m.value for m in history]
            n = len(values)
            x = list(range(n))
            
            sum_x = sum(x)
            sum_y = sum(values)
            sum_xy = sum(xi * yi for xi, yi in zip(x, values))
            sum_x_sq = sum(xi ** 2 for xi in x)
            
            denominator = n * sum_x_sq - sum_x ** 2
            if denominator == 0:
                return {"trend": "stable"}
            
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n
            
            if slope > 0.1:
                trend = "increasing"
            elif slope < -0.1:
                trend = "decreasing"
            else:
                trend = "stable"
            
            return {
                "trend": trend,
                "slope": slope,
                "intercept": intercept,
                "r_squared": 1.0 - (sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, values)) / 
                                   sum((yi - statistics.mean(values)) ** 2 for yi in values)) if n > 2 else 0.0
            }
    
    def clear(self, name: Optional[str] = None):
        """
        清除数据
        
        Args:
            name: 指标名称，None则清除所有
        """
        with self._lock:
            if name:
                if name in self.metrics:
                    del self.metrics[name]
                if name in self.stats:
                    del self.stats[name]
            else:
                self.metrics.clear()
                self.stats.clear()


# 上下文管理器装饰器
class TimedOperation:
    """计时操作上下文管理器"""
    
    def __init__(self, monitor: PerformanceMonitor, name: str, tags: Optional[Dict[str, str]] = None):
        """
        初始化
        
        Args:
            monitor: 性能监控器
            name: 操作名称
            tags: 标签
        """
        self.monitor = monitor
        self.name = name
        self.tags = tags or {}
        self.start_time = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.time() - self.start_time) * 1000  # 毫秒
        success = exc_type is None
        
        tags = dict(self.tags)
        tags["success"] = str(success)
        
        self.monitor.record(self.name, duration, "ms", tags)
        return False


# 便捷函数
def create_performance_monitor(history_size: int = 1000) -> PerformanceMonitor:
    """
    创建性能监控器
    
    Args:
        history_size: 历史记录大小
    
    Returns:
        PerformanceMonitor: 性能监控器
    """
    return PerformanceMonitor(history_size=history_size)


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("性能监控 - 快速测试")
    print("=" * 60)
    
    # 创建监控器
    monitor = create_performance_monitor()
    
    # 添加阈值规则
    monitor.add_threshold_rule(ThresholdRule(
        name="validation_time",
        threshold=100.0,
        alert_level=AlertLevel.WARNING,
        operator=">"
    ))
    
    # 添加告警监听器
    def on_alert(alert):
        print(f"\n⚠️ 收到告警: {alert.level.name} - {alert.message}")
    
    monitor.add_alert_listener(on_alert)
    
    # 记录一些指标
    print("\n1. 记录性能指标:")
    for i in range(20):
        duration = 10 + random.uniform(0, 30)  # 10-40ms
        if i == 15:
            duration = 150  # 模拟慢操作
        monitor.record("validation_time", duration, "ms", {"iteration": str(i)})
        print(f"   记录: {duration:.1f}ms")
    
    # 获取统计
    print("\n2. 性能统计:")
    stats = monitor.get_stats("validation_time")
    if stats:
        print(f"   Count: {stats.count}")
        print(f"   Min: {stats.min:.1f}ms")
        print(f"   Max: {stats.max:.1f}ms")
        print(f"   Mean: {stats.mean:.1f}ms")
        print(f"   P95: {stats.p95:.1f}ms")
        print(f"   P99: {stats.p99:.1f}ms")
    
    # 检测异常
    print("\n3. 异常检测:")
    anomalies = monitor.detect_anomalies("validation_time")
    print(f"   检测到 {len(anomalies)} 个异常")
    
    # 获取告警
    print("\n4. 告警记录:")
    alerts = monitor.get_alerts()
    print(f"   共 {len(alerts)} 条告警")
    
    # 趋势分析
    print("\n5. 趋势分析:")
    trend = monitor.get_trend("validation_time")
    print(f"   趋势: {trend['trend']}")
    if 'slope' in trend:
        print(f"   斜率: {trend['slope']:.4f}")
    
    print("\n✅ 快速测试完成!")
