"""
简单测试EndRule提取器
"""
import sys
import os

# 确保能导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from end_rule_extractor import EndRuleExtractor

print("开始测试EndRule提取器...")
extractor = EndRuleExtractor()

desc = "生成2024年度销售报告"
end_rule = extractor.extract(desc)

print("\n✓ 提取成功！")
print(f"成功条件数量: {len(end_rule.success_conditions)}")
print(f"失败条件数量: {len(end_rule.failure_conditions)}")

print("\n成功条件:")
for sc in end_rule.success_conditions:
    print(f"  - {sc.id}: {sc.description}")
    print(f"    检查规则: {sc.check_rule}")

print("\n失败条件:")
for fc in end_rule.failure_conditions:
    print(f"  - {fc.id} (优先级{fc.priority}): {fc.description}")
    print(f"    检查规则: {fc.check_rule}")

print(f"\n评估逻辑: {end_rule.evaluation_logic}")
print(f"\nis_valid: {end_rule.is_valid()}")
print("\n测试完成！")
