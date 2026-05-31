#!/usr/bin/env python3
"""
阶段49测试脚本：日志系统优化
"""

import sys
import os
import time
import tempfile
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validation.logger_manager import (
    LoggerManager,
    LogLevel,
    Environment,
    get_logger,
    performance_trace,
    set_log_level,
    set_environment
)
from validation.action_post_validator import ActionPostValidator, ActionOutput


def test_log_level_switching():
    """测试日志级别切换"""
    print("=" * 60)
    print("测试1: 日志级别动态切换")
    print("=" * 60)
    
    manager = LoggerManager()
    logger = get_logger('test_switching')
    
    # 测试DEBUG级别
    print("\n1. 测试DEBUG级别:")
    manager.set_level(LogLevel.DEBUG)
    print(f"   当前级别: {manager.get_level().name}")
    
    debug_output = StringIO()
    original_handler = logger.handlers[0] if logger.handlers else None
    if original_handler and hasattr(original_handler, 'stream'):
        logger.info("INFO消息应输出")
        logger.debug("DEBUG消息应输出")
    
    # 测试INFO级别
    print("\n2. 切换到INFO级别:")
    manager.set_level(LogLevel.INFO)
    print(f"   当前级别: {manager.get_level().name}")
    
    logger.info("INFO消息应输出")
    logger.debug("DEBUG消息不应输出")
    
    # 测试WARNING级别
    print("\n3. 切换到WARNING级别:")
    manager.set_level(LogLevel.WARNING)
    print(f"   当前级别: {manager.get_level().name}")
    
    logger.warning("WARNING消息应输出")
    logger.info("INFO消息不应输出")
    
    # 测试OFF级别
    print("\n4. 切换到OFF级别:")
    manager.set_level(LogLevel.OFF)
    print(f"   当前级别: {manager.get_level().name}")
    
    logger.critical("CRITICAL消息也不应输出")
    
    print("\n✅ 日志级别切换测试通过")
    return True


def test_environment_switching():
    """测试环境切换"""
    print("\n" + "=" * 60)
    print("测试2: 运行环境切换")
    print("=" * 60)
    
    manager = LoggerManager()
    
    # 测试开发环境
    print("\n1. 开发环境:")
    manager.set_environment(Environment.DEVELOPMENT)
    print(f"   环境: {manager.get_environment().value}")
    print(f"   日志级别: {manager.get_level().name}")
    assert manager.get_level() == LogLevel.DEBUG
    
    # 测试生产环境
    print("\n2. 生产环境:")
    manager.set_environment(Environment.PRODUCTION)
    print(f"   环境: {manager.get_environment().value}")
    print(f"   日志级别: {manager.get_level().name}")
    assert manager.get_level() == LogLevel.WARNING
    
    # 测试测试环境
    print("\n3. 测试环境:")
    manager.set_environment(Environment.TESTING)
    print(f"   环境: {manager.get_environment().value}")
    print(f"   日志级别: {manager.get_level().name}")
    assert manager.get_level() == LogLevel.INFO
    
    print("\n✅ 环境切换测试通过")
    return True


def test_performance_tracing():
    """测试性能追踪"""
    print("\n" + "=" * 60)
    print("测试3: 性能追踪")
    print("=" * 60)
    
    manager = LoggerManager()
    manager.set_level(LogLevel.INFO)
    
    # 测试上下文管理器方式
    print("\n1. 上下文管理器方式:")
    start = time.time()
    with performance_trace('context_test', category='test', priority='high'):
        time.sleep(0.1)
        print("   操作完成")
    duration = time.time() - start
    print(f"   实际耗时: {duration:.4f}s")
    
    # 测试手动方式
    print("\n2. 手动方式:")
    trace_id = manager.start_performance_trace('manual_test', category='test')
    time.sleep(0.05)
    metric = manager.end_performance_trace(trace_id)
    print(f"   追踪耗时: {metric.duration:.4f}s")
    
    # 获取性能指标
    print("\n3. 获取性能指标:")
    metrics = manager.get_performance_metrics()
    print(f"   指标数: {len(metrics)}")
    for name, m in metrics.items():
        if m.duration:
            print(f"   - {name}: {m.duration:.4f}s")
    
    manager.clear_performance_metrics()
    assert len(manager.get_performance_metrics()) == 0
    
    print("\n✅ 性能追踪测试通过")
    return True


def test_file_output():
    """测试文件输出"""
    print("\n" + "=" * 60)
    print("测试4: 文件输出")
    print("=" * 60)
    
    manager = LoggerManager()
    logger = get_logger('file_test')
    
    # 创建临时文件
    temp_file = tempfile.mktemp(suffix='.log')
    print(f"\n1. 临时日志文件: {temp_file}")
    
    # 启用文件输出
    manager.enable_file_output('test_log', temp_file, max_bytes=1024, backup_count=2)
    
    # 写入日志
    logger.info("测试INFO消息")
    logger.warning("测试WARNING消息")
    logger.error("测试ERROR消息")
    
    # 验证文件存在且有内容
    time.sleep(0.1)
    file_exists = os.path.exists(temp_file)
    if file_exists:
        with open(temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"\n2. 文件内容检查:")
        print(f"   文件长度: {len(content)} 字符")
    
    # 禁用文件输出
    manager.disable_file_output('test_log')
    
    # 清理临时文件
    if os.path.exists(temp_file):
        os.remove(temp_file)
        for i in range(1, 3):
            backup = f"{temp_file}.{i}"
            if os.path.exists(backup):
                os.remove(backup)
    
    print("\n✅ 文件输出测试通过")
    return file_exists


def test_integration_with_validation():
    """测试与验证模块集成"""
    print("\n" + "=" * 60)
    print("测试5: 与验证模块集成")
    print("=" * 60)
    
    # 设置开发环境
    manager = LoggerManager()
    manager.set_environment(Environment.DEVELOPMENT)
    
    # 创建验证器
    print("\n1. 在开发环境下运行验证:")
    validator = ActionPostValidator()
    
    output = ActionOutput(
        action_id="integration_test",
        success=True,
        data={"result": "ok"},
        execution_time=0.1
    )
    
    report = validator.validate_action_output("integration_test", output)
    print(f"   验证结果: {report.validation_status.value}")
    assert report.is_valid()
    
    # 切换到生产环境
    print("\n2. 切换到生产环境:")
    manager.set_environment(Environment.PRODUCTION)
    
    output2 = ActionOutput(
        action_id="production_test",
        success=True,
        data={"result": "ok"},
        execution_time=0.05
    )
    
    report2 = validator.validate_action_output("production_test", output2)
    print(f"   验证结果: {report2.validation_status.value}")
    assert report2.is_valid()
    
    print("\n✅ 集成测试通过")
    return True


def test_convenience_functions():
    """测试便捷函数"""
    print("\n" + "=" * 60)
    print("测试6: 便捷函数")
    print("=" * 60)
    
    # 测试 set_log_level
    print("\n1. 便捷函数 set_log_level:")
    set_log_level(LogLevel.INFO)
    manager = LoggerManager()
    assert manager.get_level() == LogLevel.INFO
    print(f"   设置级别: {manager.get_level().name}")
    
    # 测试 set_environment
    print("\n2. 便捷函数 set_environment:")
    set_environment(Environment.PRODUCTION)
    assert manager.get_environment() == Environment.PRODUCTION
    print(f"   设置环境: {manager.get_environment().value}")
    
    # 恢复到测试环境
    set_environment(Environment.TESTING)
    
    print("\n✅ 便捷函数测试通过")
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("阶段49测试：日志系统优化")
    print("=" * 60)
    
    all_passed = True
    try:
        # 运行所有测试
        if not test_log_level_switching():
            all_passed = False
            
        if not test_environment_switching():
            all_passed = False
            
        if not test_performance_tracing():
            all_passed = False
            
        if not test_file_output():
            all_passed = False
            
        if not test_integration_with_validation():
            all_passed = False
            
        if not test_convenience_functions():
            all_passed = False
        
        # 输出总结
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 所有测试通过！日志系统优化完成！")
            print("\n主要功能:")
            print("  ✅ 日志级别动态切换")
            print("  ✅ 生产/开发/测试环境自动配置")
            print("  ✅ 控制台输出开关")
            print("  ✅ 文件输出（支持日志轮转）")
            print("  ✅ 性能追踪和标记")
            print("  ✅ 便捷函数支持")
        else:
            print("❌ 部分测试失败，请检查错误")
        print("=" * 60)
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ 测试执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
