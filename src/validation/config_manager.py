"""
第四层：分段校验收敛层 - 配置管理
基于第一性原理的AI Agent任务规划系统

核心功能：
- 配置加载与保存
- 配置验证
- 配置版本管理
- 配置热更新
"""

import json
import os
import time
import hashlib
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from validation.logger_manager import get_logger

logger = get_logger('validation.config')


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigVersionMismatchError(Exception):
    """配置版本不匹配错误"""
    pass


@dataclass
class ConfigMetadata:
    """配置元数据"""
    version: str = "1.0.0"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    checksum: str = ""
    description: str = ""
    author: str = ""


@dataclass
class ValidationRule:
    """验证规则"""
    field: str
    validator: Callable[[Any], bool]
    error_message: str
    required: bool = True
    default: Any = None


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


T = TypeVar('T')


class ConfigManager(Generic[T]):
    """
    统一配置管理器
    
    功能：
    - 配置加载与保存
    - 配置验证
    - 配置版本管理
    - 配置热更新
    """
    
    def __init__(self, config_path: Optional[str] = None, auto_reload: bool = False):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
            auto_reload: 是否自动重新加载
        """
        self.config_path = config_path or self._default_config_path()
        self.config: Optional[T] = None
        self.metadata: ConfigMetadata = ConfigMetadata()
        self.validation_rules: List[ValidationRule] = []
        self.change_listeners: List[Callable[[T], None]] = []
        self._lock = threading.RLock()
        self._last_modified: float = 0
        self._auto_reload = auto_reload
        self._reload_thread: Optional[threading.Thread] = None
        self._running = False
        
        logger.info(f"✅ 配置管理器初始化完成 (path={self.config_path}, auto_reload={auto_reload})")
    
    def _default_config_path(self) -> str:
        """获取默认配置文件路径"""
        return str(Path.home() / ".ai_agent" / "config.json")
    
    def _compute_checksum(self, data: Dict[str, Any]) -> str:
        """计算配置数据的校验和"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(json_str.encode('utf-8')).hexdigest()
    
    def add_validation_rule(self, rule: ValidationRule):
        """添加验证规则"""
        self.validation_rules.append(rule)
        logger.debug(f"添加验证规则: {rule.field}")
    
    def _get_nested_value(self, config: Dict[str, Any], field: str) -> Any:
        """
        获取嵌套字段值
        
        Args:
            config: 配置字典
            field: 字段名（支持点号分隔的嵌套字段）
        
        Returns:
            Any: 字段值
        """
        parts = field.split('.')
        current = config
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        
        return current
    
    def _set_nested_value(self, config: Dict[str, Any], field: str, value: Any):
        """
        设置嵌套字段值
        
        Args:
            config: 配置字典
            field: 字段名（支持点号分隔的嵌套字段）
            value: 要设置的值
        """
        parts = field.split('.')
        current = config
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            if not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def _has_nested_value(self, config: Dict[str, Any], field: str) -> bool:
        """
        检查是否有嵌套字段
        
        Args:
            config: 配置字典
            field: 字段名（支持点号分隔的嵌套字段）
        
        Returns:
            bool: 是否有该字段
        """
        parts = field.split('.')
        current = config
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        
        return True
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """
        验证配置
        
        Args:
            config: 配置字典
        
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(valid=True)
        
        for rule in self.validation_rules:
            if not self._has_nested_value(config, rule.field):
                if rule.required:
                    result.valid = False
                    result.errors.append(f"缺少必需字段: {rule.field}")
                elif rule.default is not None:
                    self._set_nested_value(config, rule.field, rule.default)
                    result.warnings.append(f"使用默认值: {rule.field} = {rule.default}")
                continue
            
            value = self._get_nested_value(config, rule.field)
            if not rule.validator(value):
                result.valid = False
                result.errors.append(f"{rule.error_message}: {rule.field} = {value}")
        
        return result
    
    def load(self) -> Optional[T]:
        """
        加载配置
        
        Returns:
            Optional[T]: 加载的配置，失败返回None
        """
        with self._lock:
            if not os.path.exists(self.config_path):
                logger.warning(f"配置文件不存在: {self.config_path}")
                return None
            
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                config_data = data.get('config', {})
                metadata_data = data.get('metadata', {})
                
                # 验证配置
                validation_result = self.validate(config_data)
                if not validation_result.valid:
                    logger.error(f"配置验证失败: {validation_result.errors}")
                    raise ConfigValidationError(f"配置验证失败: {validation_result.errors}")
                
                for warning in validation_result.warnings:
                    logger.warning(warning)
                
                # 构建配置
                self.config = config_data
                
                # 构建元数据
                self.metadata = ConfigMetadata(
                    version=metadata_data.get('version', '1.0.0'),
                    created_at=metadata_data.get('created_at', time.time()),
                    updated_at=metadata_data.get('updated_at', time.time()),
                    checksum=metadata_data.get('checksum', ''),
                    description=metadata_data.get('description', ''),
                    author=metadata_data.get('author', '')
                )
                
                # 更新修改时间
                self._last_modified = os.path.getmtime(self.config_path)
                
                logger.info(f"✅ 配置加载成功 (version={self.metadata.version})")
                
                # 通知变更
                self._notify_change_listeners()
                
                return self.config
                
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
                return None
    
    def save(self, config: Optional[T] = None, description: str = "", author: str = "") -> bool:
        """
        保存配置
        
        Args:
            config: 要保存的配置（如果为None则使用当前配置）
            description: 配置描述
            author: 作者
        
        Returns:
            bool: 是否保存成功
        """
        with self._lock:
            config_to_save = config if config is not None else self.config
            if config_to_save is None:
                logger.warning("没有配置可保存")
                return False
            
            try:
                # 确保目录存在
                config_dir = os.path.dirname(self.config_path)
                if config_dir and not os.path.exists(config_dir):
                    os.makedirs(config_dir, exist_ok=True)
                
                # 转换为字典
                config_dict = self._to_dict(config_to_save)
                
                # 更新元数据
                old_metadata = self.metadata
                self.metadata = ConfigMetadata(
                    version=self._increment_version(old_metadata.version) if old_metadata else "1.0.0",
                    created_at=old_metadata.created_at if old_metadata else time.time(),
                    updated_at=time.time(),
                    checksum=self._compute_checksum(config_dict),
                    description=description or old_metadata.description,
                    author=author or old_metadata.author
                )
                
                # 构建保存数据
                save_data = {
                    'metadata': asdict(self.metadata),
                    'config': config_dict
                }
                
                # 备份旧配置
                self._backup_old_config()
                
                # 保存
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)
                
                self.config = config_to_save
                logger.info(f"✅ 配置保存成功 (version={self.metadata.version})")
                
                # 更新修改时间
                self._last_modified = time.time()
                
                # 通知变更
                self._notify_change_listeners()
                
                return True
                
            except Exception as e:
                logger.error(f"保存配置失败: {e}")
                return False
    
    def _to_dict(self, config: Any) -> Dict[str, Any]:
        """转换为字典"""
        if hasattr(config, 'to_dict'):
            return config.to_dict()
        elif hasattr(config, '__dict__'):
            return {k: v for k, v in config.__dict__.items() if not k.startswith('_')}
        else:
            return dict(config)
    
    def _increment_version(self, version: str) -> str:
        """递增版本号"""
        parts = version.split('.')
        if len(parts) < 3:
            return "1.0.0"
        
        try:
            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2])
            return f"{major}.{minor}.{patch + 1}"
        except ValueError:
            return "1.0.0"
    
    def _backup_old_config(self):
        """备份旧配置"""
        if not os.path.exists(self.config_path):
            return
        
        backup_path = f"{self.config_path}.bak"
        try:
            if os.path.exists(backup_path):
                # 轮换备份
                for i in range(10, 0, -1):
                    old_backup = f"{self.config_path}.bak.{i}"
                    new_backup = f"{self.config_path}.bak.{i+1}"
                    if os.path.exists(old_backup):
                        os.rename(old_backup, new_backup)
                os.rename(backup_path, f"{self.config_path}.bak.1")
            
            os.rename(self.config_path, backup_path)
            logger.debug(f"备份旧配置: {backup_path}")
        except Exception as e:
            logger.warning(f"备份旧配置失败: {e}")
    
    def add_change_listener(self, listener: Callable[[T], None]):
        """添加配置变更监听器"""
        with self._lock:
            self.change_listeners.append(listener)
            logger.debug(f"添加配置变更监听器")
    
    def remove_change_listener(self, listener: Callable[[T], None]):
        """移除配置变更监听器"""
        with self._lock:
            if listener in self.change_listeners:
                self.change_listeners.remove(listener)
                logger.debug(f"移除配置变更监听器")
    
    def _notify_change_listeners(self):
        """通知配置变更监听器"""
        if not self.config:
            return
        
        for listener in self.change_listeners:
            try:
                listener(self.config)
            except Exception as e:
                logger.error(f"配置变更监听器执行失败: {e}")
    
    def start_auto_reload(self, check_interval: float = 5.0):
        """
        启动自动重新加载
        
        Args:
            check_interval: 检查间隔（秒）
        """
        if self._running:
            logger.warning("自动重新加载已经在运行中")
            return
        
        self._running = True
        self._auto_reload = True
        
        def reload_loop():
            while self._running:
                try:
                    if os.path.exists(self.config_path):
                        mtime = os.path.getmtime(self.config_path)
                        if mtime > self._last_modified:
                            logger.info("检测到配置文件变更，重新加载...")
                            self.load()
                except Exception as e:
                    logger.error(f"检查配置文件变更失败: {e}")
                time.sleep(check_interval)
        
        self._reload_thread = threading.Thread(target=reload_loop, daemon=True)
        self._reload_thread.start()
        logger.info(f"✅ 自动重新加载已启动 (interval={check_interval}s)")
    
    def stop_auto_reload(self):
        """停止自动重新加载"""
        self._running = False
        if self._reload_thread:
            self._reload_thread.join(timeout=1.0)
            logger.info("自动重新加载已停止")
    
    def get_config(self) -> Optional[T]:
        """获取当前配置"""
        return self.config
    
    def get_metadata(self) -> ConfigMetadata:
        """获取配置元数据"""
        return self.metadata
    
    def __getitem__(self, key: str) -> Any:
        """字典式访问"""
        if self.config and hasattr(self.config, '__getitem__'):
            return self.config[key]
        elif isinstance(self.config, dict):
            return self.config[key]
        raise KeyError(key)
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        if self.config and hasattr(self.config, '__contains__'):
            return key in self.config
        elif isinstance(self.config, dict):
            return key in self.config
        return False


# 便捷函数
def create_config_manager(
    config_path: Optional[str] = None,
    auto_reload: bool = False
) -> ConfigManager:
    """
    创建配置管理器
    
    Args:
        config_path: 配置文件路径
        auto_reload: 是否自动重新加载
    
    Returns:
        ConfigManager: 配置管理器
    """
    return ConfigManager(config_path, auto_reload)


def get_validation_system_config_rules() -> List[ValidationRule]:
    """获取验证系统默认配置规则"""
    return [
        ValidationRule(
            field="logger.level",
            validator=lambda x: x in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF"],
            error_message="日志级别必须是 DEBUG/INFO/WARNING/ERROR/CRITICAL/OFF",
            required=False,
            default="INFO"
        ),
        ValidationRule(
            field="logger.console_output",
            validator=lambda x: isinstance(x, bool),
            error_message="console_output 必须是布尔值",
            required=False,
            default=True
        ),
        ValidationRule(
            field="history.max_records",
            validator=lambda x: isinstance(x, int) and x > 0,
            error_message="max_records 必须是大于0的整数",
            required=False,
            default=10000
        ),
        ValidationRule(
            field="history.cleanup_strategy",
            validator=lambda x: x in ["FIFO", "LRU"],
            error_message="cleanup_strategy 必须是 FIFO/LRU",
            required=False,
            default="FIFO"
        ),
        ValidationRule(
            field="validation.thresholds.match_score",
            validator=lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
            error_message="match_score 必须是0-1之间的数值",
            required=False,
            default=0.7
        ),
        ValidationRule(
            field="validation.thresholds.drift_score",
            validator=lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
            error_message="drift_score 必须是0-1之间的数值",
            required=False,
            default=0.3
        ),
        ValidationRule(
            field="circuit_breaker.failure_threshold",
            validator=lambda x: isinstance(x, int) and x > 0,
            error_message="failure_threshold 必须是大于0的整数",
            required=False,
            default=10
        ),
        ValidationRule(
            field="circuit_breaker.reset_timeout",
            validator=lambda x: isinstance(x, (int, float)) and x > 0,
            error_message="reset_timeout 必须是大于0的数值",
            required=False,
            default=30.0
        )
    ]


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("配置管理 - 快速测试")
    print("=" * 60)
    
    # 创建临时配置文件
    import tempfile
    temp_config = tempfile.mktemp(suffix='.json')
    
    # 创建管理器
    manager = create_config_manager(temp_config, auto_reload=False)
    
    # 添加验证规则
    for rule in get_validation_system_config_rules():
        manager.add_validation_rule(rule)
    
    # 创建示例配置
    test_config = {
        "logger": {
            "level": "INFO",
            "console_output": True
        },
        "history": {
            "max_records": 10000,
            "cleanup_strategy": "FIFO"
        },
        "validation": {
            "thresholds": {
                "match_score": 0.7,
                "drift_score": 0.3
            }
        },
        "circuit_breaker": {
            "failure_threshold": 10,
            "reset_timeout": 30.0
        }
    }
    
    # 保存配置
    print("\n1. 保存配置:")
    if manager.save(test_config, description="验证系统配置", author="System"):
        print("   ✅ 配置保存成功")
    
    # 加载配置
    print("\n2. 加载配置:")
    loaded_config = manager.load()
    if loaded_config:
        print(f"   ✅ 配置加载成功")
        print(f"   日志级别: {loaded_config['logger']['level']}")
        print(f"   最大记录: {loaded_config['history']['max_records']}")
    
    # 获取元数据
    print("\n3. 配置元数据:")
    metadata = manager.get_metadata()
    print(f"   版本: {metadata.version}")
    print(f"   创建时间: {datetime.fromtimestamp(metadata.created_at)}")
    print(f"   校验和: {metadata.checksum}")
    
    # 验证
    print("\n4. 验证:")
    validation_result = manager.validate(test_config)
    print(f"   有效: {validation_result.valid}")
    if validation_result.warnings:
        print(f"   警告: {len(validation_result.warnings)} 条")
    
    print("\n✅ 快速测试完成!")
    
    # 清理临时文件
    if os.path.exists(temp_config):
        os.remove(temp_config)
