# 阶段51测试：配置管理
# 基于第一性原理的AI Agent任务规划系统

import sys
import os
import tempfile
import time
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validation.config_manager import (
    create_config_manager,
    ConfigManager,
    ValidationRule,
    ValidationResult,
    ConfigMetadata,
    get_validation_system_config_rules
)
from validation.logger_manager import get_logger

logger = get_logger('test.stage51')


def test_config_load_save():
    """测试配置加载和保存"""
    print("\n" + "=" * 60)
    print("测试1: 配置加载和保存")
    print("=" * 60)
    
    # 创建临时配置文件
    temp_config = tempfile.mktemp(suffix='.json')
    
    try:
        # 创建管理器
        manager = create_config_manager(temp_config)
        
        # 创建测试配置
        test_config = {
            "test": {
                "key": "value",
                "number": 42
            }
        }
        
        # 保存配置
        print("\n1.1 保存配置:")
        if manager.save(test_config, description="测试配置", author="Test"):
            print("   ✅ 配置保存成功")
        else:
            print("   ❌ 配置保存失败")
            return False
        
        # 检查文件存在
        if os.path.exists(temp_config):
            print("   ✅ 配置文件创建成功")
        else:
            print("   ❌ 配置文件创建失败")
            return False
        
        # 加载配置
        print("\n1.2 加载配置:")
        loaded_config = manager.load()
        if loaded_config:
            print("   ✅ 配置加载成功")
            print(f"   test.key: {loaded_config['test']['key']}")
            print(f"   test.number: {loaded_config['test']['number']}")
        else:
            print("   ❌ 配置加载失败")
            return False
        
        return True
        
    finally:
        if os.path.exists(temp_config):
            os.remove(temp_config)
            for i in range(1, 10):
                backup = f"{temp_config}.bak.{i}"
                if os.path.exists(backup):
                    os.remove(backup)


def test_config_validation():
    """测试配置验证"""
    print("\n" + "=" * 60)
    print("测试2: 配置验证")
    print("=" * 60)
    
    temp_config = tempfile.mktemp(suffix='.json')
    
    try:
        manager = create_config_manager(temp_config)
        
        # 添加验证规则
        manager.add_validation_rule(ValidationRule(
            field="test.required",
            validator=lambda x: x is not None,
            error_message="required 字段不能为空",
            required=True
        ))
        manager.add_validation_rule(ValidationRule(
            field="test.optional",
            validator=lambda x: isinstance(x, int),
            error_message="optional 必须是整数",
            required=False,
            default=100
        ))
        
        # 测试缺失必需字段
        print("\n2.1 测试缺失必需字段:")
        bad_config = {"test": {}}
        result = manager.validate(bad_config)
        print(f"   验证通过: {result.valid}")
        print(f"   错误数: {len(result.errors)}")
        print(f"   警告数: {len(result.warnings)}")
        
        if not result.valid and len(result.errors) > 0:
            print("   ✅ 缺失字段正确检测")
        else:
            print("   ❌ 缺失字段检测失败")
            return False
        
        # 测试有效配置
        print("\n2.2 测试有效配置:")
        good_config = {"test": {"required": "value", "optional": 200}}
        result = manager.validate(good_config)
        print(f"   验证通过: {result.valid}")
        
        if result.valid:
            print("   ✅ 有效配置正确通过")
        else:
            print("   ❌ 有效配置验证失败")
            return False
        
        return True
        
    finally:
        if os.path.exists(temp_config):
            os.remove(temp_config)


def test_config_version():
    """测试配置版本管理"""
    print("\n" + "=" * 60)
    print("测试3: 配置版本管理")
    print("=" * 60)
    
    temp_config = tempfile.mktemp(suffix='.json')
    
    try:
        manager = create_config_manager(temp_config)
        
        # 第一次保存
        config1 = {"version": 1}
        manager.save(config1, description="版本1", author="Test")
        metadata1 = manager.get_metadata()
        print(f"\n3.1 第一次保存版本: {metadata1.version}")
        
        # 第二次保存
        config2 = {"version": 2}
        manager.save(config2, description="版本2", author="Test")
        metadata2 = manager.get_metadata()
        print(f"3.2 第二次保存版本: {metadata2.version}")
        
        # 检查版本递增
        if metadata2.version > metadata1.version:
            print("   ✅ 版本号正确递增")
        else:
            print(f"   ❌ 版本号递增失败: {metadata1.version} -> {metadata2.version}")
            return False
        
        # 检查校验和不同
        if metadata1.checksum != metadata2.checksum:
            print("   ✅ 校验和不同（配置变更正确识别）")
        else:
            print("   ❌ 校验和问题")
            return False
        
        return True
        
    finally:
        if os.path.exists(temp_config):
            os.remove(temp_config)
            for i in range(1, 10):
                backup = f"{temp_config}.bak.{i}"
                if os.path.exists(backup):
                    os.remove(backup)


def test_config_listeners():
    """测试配置变更监听器"""
    print("\n" + "=" * 60)
    print("测试4: 配置变更监听器")
    print("=" * 60)
    
    temp_config = tempfile.mktemp(suffix='.json')
    changes_detected = []
    
    try:
        manager = create_config_manager(temp_config)
        
        # 添加监听器
        def on_change(config):
            changes_detected.append(config)
            print(f"   监听器触发: {config}")
        
        manager.add_change_listener(on_change)
        
        # 保存配置，应该触发监听器
        print("\n4.1 保存配置触发监听器:")
        manager.save({"test": "value1"}, description="测试1", author="Test")
        
        time.sleep(0.1)  # 等待监听器
        
        if len(changes_detected) == 1:
            print("   ✅ 监听器正确触发")
        else:
            print(f"   ❌ 监听器触发次数错误: {len(changes_detected)}")
            return False
        
        # 移除监听器
        manager.remove_change_listener(on_change)
        
        # 再次保存，不应触发
        print("\n4.2 移除监听器后保存:")
        manager.save({"test": "value2"}, description="测试2", author="Test")
        time.sleep(0.1)
        
        if len(changes_detected) == 1:
            print("   ✅ 监听器正确移除")
        else:
            print("   ❌ 监听器移除失败")
            return False
        
        return True
        
    finally:
        if os.path.exists(temp_config):
            os.remove(temp_config)


def test_validation_system_config_rules():
    """测试验证系统默认配置规则"""
    print("\n" + "=" * 60)
    print("测试5: 验证系统默认配置规则")
    print("=" * 60)
    
    temp_config = tempfile.mktemp(suffix='.json')
    
    try:
        manager = create_config_manager(temp_config)
        
        # 添加默认规则
        rules = get_validation_system_config_rules()
        for rule in rules:
            manager.add_validation_rule(rule)
        
        print(f"\n5.1 加载了 {len(rules)} 个默认验证规则")
        
        # 创建有效配置
        valid_config = {
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
        
        result = manager.validate(valid_config)
        print(f"5.2 有效配置验证: {result.valid}")
        
        if result.valid:
            print("   ✅ 有效配置正确验证")
        else:
            print(f"   ❌ 有效配置验证失败: {result.errors}")
            return False
        
        return True
        
    finally:
        if os.path.exists(temp_config):
            os.remove(temp_config)


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("🚀 阶段51测试：配置管理")
    print("=" * 80)
    
    all_passed = True
    tests = [
        ("配置加载和保存", test_config_load_save),
        ("配置验证", test_config_validation),
        ("配置版本管理", test_config_version),
        ("配置变更监听器", test_config_listeners),
        ("验证系统默认配置规则", test_validation_system_config_rules)
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
        print("🎉 所有测试通过！配置管理功能完整！")
    else:
        print("❌ 部分测试失败，请检查")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
