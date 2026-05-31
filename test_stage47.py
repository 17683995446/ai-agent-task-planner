#!/usr/bin/env python3
"""
阶段47测试脚本：目标对齐预校验
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validation.target_alignment import (
    TargetAlignmentValidator,
    AlignmentStatus,
    DriftType,
    quick_align_check
)


def test_target_definition():
    """测试目标定义"""
    print("=" * 60)
    print("测试1: 目标定义与解析")
    print("=" * 60)
    
    validator = TargetAlignmentValidator()
    
    # 定义目标（使用明确的关键词）
    target = validator.define_target(
        target_id="test_goal",
        target_text="销售数据分析报告",
        scope_keywords=["销售", "分析", "报告", "数据"],
        anti_keywords=["投诉", "退货"]
    )
    
    print(f"\n目标ID: {target.target_id}")
    print(f"原始文本: {target.target_text}")
    print(f"提取关键词: {target.target_keywords}")
    print(f"实体列表: {target.target_entities}")
    print(f"范围边界: {target.scope_boundary}")
    print(f"反向关键词: {target.anti_keywords}")
    
    assert target.target_id == "test_goal"
    assert len(target.target_keywords) > 0
    assert "销售" in target.scope_boundary, "scope_keywords应该包含销售"
    
    print("\n✅ 目标定义测试通过!")


def test_basic_alignment():
    """测试基本对齐验证"""
    print("\n" + "=" * 60)
    print("测试2: 基本对齐验证")
    print("=" * 60)
    
    validator = TargetAlignmentValidator()
    
    # 定义目标（使用scope_keywords明确指定关键词）
    validator.define_target(
        target_id="sales_report",
        target_text="销售分析报告生成",
        scope_keywords=["销售", "分析", "报告", "数据", "读取", "生成"],
        anti_keywords=["投诉", "退货"]
    )
    
    # 验证对齐的动作
    aligned_action = "读取销售数据并生成分析报告"
    report = validator.validate_alignment(
        target_id="sales_report",
        action_text=aligned_action
    )
    
    print(f"\n动作: {aligned_action}")
    print(f"匹配度: {report.metrics.match_score:.2f}")
    print(f"偏离度: {report.metrics.drift_score:.2f}")
    print(f"覆盖率: {report.metrics.coverage_score:.2f}")
    print(f"对齐状态: {report.metrics.alignment_status.value}")
    print(f"是否阻止: {report.should_block}")
    
    assert report.metrics.match_score >= 0.5, "应该匹配"
    assert not report.should_block, "不应该阻止"
    
    print("\n✅ 基本对齐验证测试通过!")


def test_drift_detection():
    """测试偏离检测"""
    print("\n" + "=" * 60)
    print("测试3: 偏离检测")
    print("=" * 60)
    
    validator = TargetAlignmentValidator(
        match_threshold=0.6,
        drift_threshold=0.3
    )
    
    # 定义目标
    validator.define_target(
        target_id="sales_goal",
        target_text="生成销售数据分析报告",
        scope_keywords=["销售", "分析", "报告"],
        anti_keywords=["投诉", "退货"]
    )
    
    # 测试偏离的动作
    drifted_action = "处理客户投诉和退货请求"
    report = validator.validate_alignment(
        target_id="sales_goal",
        action_text=drifted_action
    )
    
    print(f"\n偏离的动作: {drifted_action}")
    print(f"匹配度: {report.metrics.match_score:.2f}")
    print(f"偏离度: {report.metrics.drift_score:.2f}")
    print(f"对齐状态: {report.metrics.alignment_status.value}")
    print(f"是否阻止: {report.should_block}")
    
    if report.drift_detected:
        print(f"检测到的偏离类型:")
        for drift in report.drift_detected:
            print(f"  - {drift.value}")
    
    if report.warnings:
        print(f"警告信息:")
        for warning in report.warnings:
            print(f"  ⚠️ {warning}")
    
    assert report.should_block, "应该阻止偏离的动作"
    
    print("\n✅ 偏离检测测试通过!")


def test_alignment_feedback():
    """测试对齐反馈"""
    print("\n" + "=" * 60)
    print("测试4: 对齐反馈生成")
    print("=" * 60)
    
    validator = TargetAlignmentValidator()
    
    # 定义目标
    validator.define_target(
        target_id="test_feedback",
        target_text="生成销售数据分析报告"
    )
    
    # 测试动作
    action = "生成报告"
    report = validator.validate_alignment(
        target_id="test_feedback",
        action_text=action
    )
    
    print(f"\n动作: {action}")
    print(f"匹配度: {report.metrics.match_score:.2f}")
    
    if report.warnings:
        print(f"\n警告:")
        for w in report.warnings:
            print(f"  ⚠️ {w}")
    
    if report.suggestions:
        print(f"\n建议:")
        for s in report.suggestions:
            print(f"  💡 {s}")
    
    print("\n✅ 对齐反馈测试通过!")


def test_quick_align_check():
    """测试快速对齐检查"""
    print("\n" + "=" * 60)
    print("测试5: 快速对齐检查")
    print("=" * 60)
    
    # 正常情况（匹配度高）
    score, is_aligned, suggestions = quick_align_check(
        target_text="生成销售数据分析报告",
        action_text="读取销售数据并生成详细的销售数据分析报告",
        match_threshold=0.6
    )
    
    print(f"\n正常情况:")
    print(f"  匹配度: {score:.2f}")
    print(f"  是否对齐: {is_aligned}")
    
    assert is_aligned, "应该对齐"
    
    # 偏离情况
    score2, is_aligned2, suggestions2 = quick_align_check(
        target_text="生成销售报告",
        action_text="处理投诉",
        match_threshold=0.6
    )
    
    print(f"\n偏离情况:")
    print(f"  匹配度: {score2:.2f}")
    print(f"  是否对齐: {is_aligned2}")
    
    assert not is_aligned2, "不应该对齐"
    
    print("\n✅ 快速对齐检查测试通过!")


def test_alignment_trend():
    """测试对齐趋势"""
    print("\n" + "=" * 60)
    print("测试6: 对齐趋势分析")
    print("=" * 60)
    
    validator = TargetAlignmentValidator()
    
    # 定义目标
    validator.define_target(
        target_id="trend_test",
        target_text="生成销售数据分析报告"
    )
    
    # 执行多次验证
    actions = [
        "读取销售数据",
        "统计分析销售数据",
        "生成分析报告"
    ]
    
    for action in actions:
        validator.validate_alignment("trend_test", action)
    
    # 获取趋势
    trend = validator.get_alignment_trend("trend_test", limit=5)
    
    print(f"\n对齐趋势:")
    print(f"  检查次数: {trend['total_checks']}")
    print(f"  平均匹配度: {trend['average_match_score']:.2f}")
    print(f"  平均偏离度: {trend['average_drift_score']:.2f}")
    print(f"  匹配趋势: {trend['match_trend']}")
    
    assert trend['total_checks'] == 3, "应该有3次检查"
    
    print("\n✅ 对齐趋势测试通过!")


def test_comprehensive_validation():
    """测试综合验证"""
    print("\n" + "=" * 60)
    print("测试7: 综合验证（目标对齐 + 分段验证）")
    print("=" * 60)
    
    from validation.segment_validator import SegmentValidator
    
    # 创建基础验证器
    base_validator = SegmentValidator()
    
    # 创建目标对齐验证器
    validator = TargetAlignmentValidator(
        base_validator=base_validator
    )
    
    # 定义目标
    validator.define_target(
        target_id="comprehensive_test",
        target_text="生成销售数据分析报告"
    )
    
    # 综合验证
    alignment_report, validation_report = validator.validate_with_segment_validator(
        target_id="comprehensive_test",
        action_text="读取销售数据并生成报告",
        action_context={
            "action_id": "action_001",
            "inputs": {"data": "sales_data"},
            "dependencies_ready": True
        }
    )
    
    print(f"\n目标对齐报告:")
    print(f"  对齐状态: {alignment_report.metrics.alignment_status.value}")
    print(f"  匹配度: {alignment_report.metrics.match_score:.2f}")
    print(f"  是否阻止: {alignment_report.should_block}")
    
    print(f"\n分段验证报告:")
    print(f"  验证结果: {validation_report.result.value}")
    print(f"  是否通过: {validation_report.is_passed()}")
    
    print("\n✅ 综合验证测试通过!")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("阶段47测试：目标对齐预校验")
    print("=" * 60)
    
    try:
        test_target_definition()
        test_basic_alignment()
        test_drift_detection()
        test_alignment_feedback()
        test_quick_align_check()
        test_alignment_trend()
        test_comprehensive_validation()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过! 阶段47完成!")
        print("=" * 60)
        print("\n📊 第四层分段验证框架功能增强!")
        print("🎯 总体进度: 47/100 (47%)")
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
