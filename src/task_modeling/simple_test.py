"""
简单测试边界约束提取修复
"""
from boundary_extractor import BoundaryExtractor

extractor = BoundaryExtractor()

# 测试修复
desc = "生成2024年度销售报告，包含中国区数据，不包含海外业务，需要在2小时内完成"
boundary = extractor.extract(desc)

print("测试描述:", desc)
print("范围包含:", boundary.scope.inclusions)
print("范围排除:", boundary.scope.exclusions)
print("最大时间:", boundary.resources.max_time_seconds, "秒")
