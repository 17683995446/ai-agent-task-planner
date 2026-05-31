#!/usr/bin/env python3
"""
架构依赖关系验证脚本
检查所有模块是否符合四层架构单向依赖规范
"""

import sys
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
import re


@dataclass
class ImportCheckResult:
    """导入检查结果"""
    module_path: str
    layer: str
    is_valid: bool = True
    issues: List[str] = field(default_factory=list)


class ArchitectureDependencyChecker:
    """架构依赖关系检查器"""

    # 四层架构定义
    LAYERS = {
        'task_modeling': 1,  # 第1层
        'topology': 2,       # 第2层
        'atomic_actions': 3,  # 第3层
        'validation': 4,     # 第4层
        'decomposition': 5,   # 整合层
    }

    def __init__(self, src_dir: str):
        self.src_dir = Path(src_dir)
        self.results: List[ImportCheckResult] = []

    def get_layer(self, module_path: Path) -> str:
        """获取模块所属层"""
        for layer in self.LAYERS.keys():
            if layer in module_path.parts:
                return layer
        return 'unknown'

    def get_layer_number(self, layer: str) -> int:
        """获取层号"""
        return self.LAYERS.get(layer, 0)

    def check_module(self, file_path: Path) -> ImportCheckResult:
        """检查单个模块的导入"""
        layer = self.get_layer(file_path)
        result = ImportCheckResult(
            module_path=str(file_path),
            layer=layer
        )

        if layer == 'unknown':
            result.is_valid = False
            result.issues.append(f"模块 {file_path} 不属于任何已知层")
            return result

        current_layer_num = self.get_layer_number(layer)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查导入语句
        import_pattern = re.compile(
            r'^(?:from|import)\s+([a-zA-Z_.]+)',
            re.MULTILINE
        )

        for match in import_pattern.finditer(content):
            import_name = match.group(1)

            # 检查是否是业务层的导入
            for imported_layer in self.LAYERS.keys():
                if import_name.startswith(imported_layer):
                    imported_layer_num = self.get_layer_number(imported_layer)

                    # 检查是否是反向依赖
                    if layer != 'decomposition' and imported_layer_num > current_layer_num:
                        result.is_valid = False
                        result.issues.append(
                            f"发现反向依赖：{layer} (第{current_layer_num}层) "
                            f"依赖 {imported_layer} (第{imported_layer_num}层) "
                            f"在 {file_path}:{content[:match.start()].count(chr(10)) + 1}"
                        )

                    # 检查第1层是否依赖其他层
                    if layer == 'task_modeling' and imported_layer != 'task_modeling':
                        result.is_valid = False
                        result.issues.append(
                            f"第1层 (task_modeling) 不应该依赖其他业务层："
                            f"{import_name} 在 {file_path}"
                        )

        return result

    def check_all(self) -> List[ImportCheckResult]:
        """检查所有模块"""
        self.results = []

        # 遍历所有 Python 文件
        for file_path in self.src_dir.rglob('*.py'):
            if file_path.name.startswith('__'):  # 跳过 __init__.py 等
                continue
            if 'test' in file_path.name.lower():  # 跳过测试文件
                continue

            result = self.check_module(file_path)
            self.results.append(result)

        return self.results

    def print_summary(self):
        """打印检查总结"""
        print("=" * 80)
        print("四层架构依赖关系检查报告")
        print("=" * 80)

        total_modules = len(self.results)
        valid_modules = sum(1 for r in self.results if r.is_valid)
        invalid_modules = total_modules - valid_modules

        print(f"\n总模块数: {total_modules}")
        print(f"✅ 符合规范: {valid_modules}")
        print(f"❌ 存在问题: {invalid_modules}")

        if invalid_modules > 0:
            print("\n" + "=" * 80)
            print("问题详情:")
            print("=" * 80)

            for result in self.results:
                if not result.is_valid:
                    print(f"\n模块: {result.module_path} (层: {result.layer})")
                    for issue in result.issues:
                        print(f"  - {issue}")

        print("\n" + "=" * 80)
        if invalid_modules == 0:
            print("✅ 所有模块符合单向依赖规范！")
            print("=" * 80)
            return True
        else:
            print(f"❌ 发现 {invalid_modules} 个模块存在依赖问题")
            print("=" * 80)
            return False


def main():
    """主函数"""
    src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')

    checker = ArchitectureDependencyChecker(src_dir)
    checker.check_all()
    is_valid = checker.print_summary()

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
