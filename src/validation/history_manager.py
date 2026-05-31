"""
第四层：分段校验收敛层 - 历史记录管理
基于第一性原理的AI Agent任务规划系统

核心功能：
- 历史记录上限控制
- 自动清理机制（FIFO/LRU）
- 导出功能（JSON/CSV）
- 查询和索引功能
"""

import json
import csv
import time
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import OrderedDict
import threading
from io import StringIO

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from validation.logger_manager import get_logger

logger = get_logger('validation.history')


class CleanupStrategy(Enum):
    """清理策略"""
    FIFO = "fifo"      # 先进先出
    LRU = "lru"        # 最近最少使用


class ExportFormat(Enum):
    """导出格式"""
    JSON = "json"
    CSV = "csv"


@dataclass
class HistoryConfig:
    """历史记录配置"""
    max_records: int = 10000              # 最大记录数
    cleanup_strategy: CleanupStrategy = CleanupStrategy.FIFO  # 清理策略
    auto_cleanup_threshold: float = 0.9   # 自动清理阈值（90%时触发）
    enable_index: bool = True             # 是否启用索引
    cleanup_on_exit: bool = False         # 退出时清理


class HistoryRecord:
    """历史记录基类"""
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryRecord':
        """从字典创建"""
        return cls(**data)


class HistoryManager:
    """
    统一历史记录管理器
    
    功能：
    - 记录上限控制
    - 自动清理机制
    - 导出功能
    - 查询和索引
    """
    
    def __init__(self, config: Optional[HistoryConfig] = None):
        """
        初始化历史记录管理器
        
        Args:
            config: 历史记录配置
        """
        self.config = config or HistoryConfig()
        self._records: List[Any] = []
        self._index: Dict[str, List[int]] = {}  # 索引：字段值 -> 记录索引列表
        self._access_order: OrderedDict[int, float] = OrderedDict()  # LRU访问顺序
        self._lock = threading.RLock()
        
        logger.info(f"✅ 历史记录管理器初始化完成 (max_records={self.config.max_records}, strategy={self.config.cleanup_strategy.value})")
    
    def add(self, record: Any) -> int:
        """
        添加历史记录
        
        Args:
            record: 历史记录
        
        Returns:
            int: 记录索引
        """
        with self._lock:
            # 检查是否需要清理
            self._auto_cleanup_if_needed()
            
            # 添加记录
            index = len(self._records)
            self._records.append(record)
            
            # 更新LRU
            if self.config.cleanup_strategy == CleanupStrategy.LRU:
                self._access_order[index] = time.time()
            
            # 更新索引
            if self.config.enable_index:
                self._update_index(record, index)
            
            logger.debug(f"添加历史记录 #{index}")
            
            return index
    
    def _auto_cleanup_if_needed(self):
        """自动清理（如果需要）"""
        if len(self._records) >= self.config.max_records * self.config.auto_cleanup_threshold:
            self._cleanup()
    
    def _cleanup(self):
        """执行清理"""
        if not self._records:
            return
        
        logger.info(f"开始清理历史记录 (当前: {len(self._records)}, 目标: {self.config.max_records})")
        
        if self.config.cleanup_strategy == CleanupStrategy.FIFO:
            # 先进先出：删除最老的记录
            remove_count = len(self._records) - int(self.config.max_records * 0.5)  # 清理到50%
            if remove_count > 0:
                self._records = self._records[remove_count:]
                logger.info(f"FIFO清理完成，移除 {remove_count} 条记录")
        
        elif self.config.cleanup_strategy == CleanupStrategy.LRU:
            # 最近最少使用：删除访问时间最早的
            remove_count = len(self._records) - int(self.config.max_records * 0.5)
            if remove_count > 0:
                indices_to_remove = list(self._access_order.keys())[:remove_count]
                self._records = [r for i, r in enumerate(self._records) if i not in indices_to_remove]
                for idx in indices_to_remove:
                    if idx in self._access_order:
                        del self._access_order[idx]
                logger.info(f"LRU清理完成，移除 {remove_count} 条记录")
        
        # 重建索引
        if self.config.enable_index:
            self._rebuild_index()
    
    def _update_index(self, record: Any, index: int):
        """更新索引"""
        record_dict = self._to_dict(record)
        
        # 索引常用字段
        index_fields = ['action_id', 'checkpoint_id', 'timestamp', 'result']
        for field_name in index_fields:
            if field_name in record_dict:
                field_value = str(record_dict[field_name])
                if field_value not in self._index:
                    self._index[field_value] = []
                self._index[field_value].append(index)
    
    def _to_dict(self, record: Any) -> Dict[str, Any]:
        """将记录转换为字典"""
        if hasattr(record, 'to_dict'):
            return record.to_dict()
        elif hasattr(record, '__dict__'):
            return record.__dict__
        else:
            return {}
    
    def _rebuild_index(self):
        """重建索引"""
        self._index.clear()
        for i, record in enumerate(self._records):
            self._update_index(record, i)
    
    def access(self, index: int) -> Optional[Any]:
        """
        访问记录（更新LRU顺序）
        
        Args:
            index: 记录索引
        
        Returns:
            Optional[Any]: 记录，如果不存在返回None
        """
        with self._lock:
            if 0 <= index < len(self._records):
                record = self._records[index]
                
                # 更新LRU顺序
                if self.config.cleanup_strategy == CleanupStrategy.LRU:
                    if index in self._access_order:
                        self._access_order.move_to_end(index)
                    else:
                        self._access_order[index] = time.time()
                
                return record
            return None
    
    def get(self, index: int) -> Optional[Any]:
        """获取记录（不更新LRU顺序）"""
        with self._lock:
            if 0 <= index < len(self._records):
                return self._records[index]
            return None
    
    def get_all(self) -> List[Any]:
        """获取所有记录"""
        with self._lock:
            return self._records.copy()
    
    def get_range(self, start: int, end: int) -> List[Any]:
        """获取指定范围的记录"""
        with self._lock:
            return self._records[start:end]
    
    def get_recent(self, count: int) -> List[Any]:
        """获取最近的N条记录"""
        with self._lock:
            return self._records[-count:] if count > 0 else []
    
    def query(self, predicate: Callable[[Any], bool]) -> List[Any]:
        """
        查询记录
        
        Args:
            predicate: 查询条件
        
        Returns:
            List[Any]: 符合条件的记录
        """
        with self._lock:
            return [r for r in self._records if predicate(r)]
    
    def query_by_field(self, field_name: str, value: Any) -> List[Any]:
        """
        按字段查询（使用索引）
        
        Args:
            field_name: 字段名
            value: 字段值
        
        Returns:
            List[Any]: 符合条件的记录
        """
        with self._lock:
            if self.config.enable_index:
                str_value = str(value)
                if str_value in self._index:
                    indices = self._index[str_value]
                    return [self._records[i] for i in indices if i < len(self._records)]
            
            # 回退到全表查询
            return [
                r for r in self._records
                if hasattr(r, field_name) and getattr(r, field_name) == value
            ]
    
    def export(self, format: ExportFormat = ExportFormat.JSON) -> str:
        """
        导出历史记录
        
        Args:
            format: 导出格式
        
        Returns:
            str: 导出内容
        """
        with self._lock:
            if format == ExportFormat.JSON:
                return self._export_json()
            elif format == ExportFormat.CSV:
                return self._export_csv()
            return ""
    
    def _export_json(self) -> str:
        """导出为JSON格式"""
        records_data = []
        for record in self._records:
            records_data.append(self._to_dict(record))
        
        return json.dumps(records_data, indent=2, ensure_ascii=False, default=str)
    
    def _export_csv(self) -> str:
        """导出为CSV格式"""
        if not self._records:
            return ""
        
        # 获取字段名
        first_record = self._records[0]
        fieldnames = list(self._to_dict(first_record).keys())
        
        # 生成CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in self._records:
            writer.writerow(self._to_dict(record))
        
        return output.getvalue()
    
    def import_records(self, data: str, format: ExportFormat = ExportFormat.JSON) -> int:
        """
        导入历史记录
        
        Args:
            data: 导入数据
            format: 数据格式
        
        Returns:
            int: 导入的记录数
        """
        try:
            if format == ExportFormat.JSON:
                return self._import_json(data)
            elif format == ExportFormat.CSV:
                return self._import_csv(data)
            return 0
        except Exception as e:
            logger.error(f"导入失败: {e}")
            return 0
    
    def _import_json(self, data: str) -> int:
        """从JSON导入"""
        records = json.loads(data)
        count = 0
        for record_dict in records:
            if isinstance(record_dict, dict):
                self.add(record_dict)
                count += 1
        return count
    
    def _import_csv(self, data: str) -> int:
        """从CSV导入"""
        input_stream = StringIO(data)
        reader = csv.DictReader(input_stream)
        count = 0
        for row in reader:
            self.add(row)
            count += 1
        return count
    
    def clear(self):
        """清空所有历史记录"""
        with self._lock:
            self._records.clear()
            self._index.clear()
            self._access_order.clear()
            logger.info("历史记录已清空")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "total_records": len(self._records),
                "max_records": self.config.max_records,
                "usage_ratio": len(self._records) / self.config.max_records if self.config.max_records > 0 else 0,
                "cleanup_strategy": self.config.cleanup_strategy.value,
                "index_enabled": self.config.enable_index,
                "index_size": len(self._index)
            }
    
    def __len__(self) -> int:
        """获取记录数"""
        with self._lock:
            return len(self._records)
    
    def __contains__(self, item: Any) -> bool:
        """检查记录是否存在"""
        with self._lock:
            return item in self._records


# 便捷函数
def create_history_manager(
    max_records: int = 10000,
    strategy: CleanupStrategy = CleanupStrategy.FIFO
) -> HistoryManager:
    """
    创建历史记录管理器
    
    Args:
        max_records: 最大记录数
        strategy: 清理策略
    
    Returns:
        HistoryManager: 历史记录管理器
    """
    config = HistoryConfig(
        max_records=max_records,
        cleanup_strategy=strategy
    )
    return HistoryManager(config)


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("历史记录管理 - 快速测试")
    print("=" * 60)
    
    # 创建管理器（LRU策略，最多100条）
    config = HistoryConfig(
        max_records=100,
        cleanup_strategy=CleanupStrategy.LRU,
        auto_cleanup_threshold=0.8
    )
    manager = HistoryManager(config)
    
    # 添加记录
    print("\n1. 添加记录:")
    for i in range(150):  # 超过最大记录数
        record = {"id": i, "action": f"action_{i}", "timestamp": time.time()}
        manager.add(record)
    
    stats = manager.get_statistics()
    print(f"   总记录数: {stats['total_records']}")
    print(f"   使用率: {stats['usage_ratio']:.1%}")
    
    # 访问记录（更新LRU）
    print("\n2. 访问记录:")
    record = manager.access(50)
    if record:
        print(f"   访问记录 #{record['id']}")
    
    # 查询记录
    print("\n3. 查询记录:")
    results = manager.query(lambda r: r.get('id', 0) > 90)
    print(f"   找到 {len(results)} 条 id > 90 的记录")
    
    # 导出
    print("\n4. 导出测试:")
    json_data = manager.export(ExportFormat.JSON)
    print(f"   JSON导出长度: {len(json_data)} 字符")
    
    # 统计
    print("\n5. 统计信息:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ 快速测试完成!")
