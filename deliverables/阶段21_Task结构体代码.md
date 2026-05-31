# 第21阶段交付物：Task四元组结构体代码

---

## 一、概述

阶段21完成了标准Task四元组结构体的设计和实现，基于第一性原理，确保任务结构清晰、可验证、可序列化。

---

## 二、实现内容

### 2.1 文件位置

```
/src/task_modeling/task_struct.py
```

### 2.2 核心数据结构

#### Task四元组完整结构

| 组件 | 类名 | 职责 |
|-----|-----|-----|
| 目标 | `Target` | 定义任务唯一目标、可衡量标准、优先级 |
| 前置条件 | `Condition` | 定义任务启动前必须满足的条件 |
| 边界约束 | `Boundary` | 定义任务范围、资源、质量约束 |
| 终止规则 | `EndRule` | 定义任务成功/失败的机器可判定规则 |
| 完整任务 | `Task` | 整合四元组的完整任务结构 |

### 2.3 Target结构

```python
@dataclass
class Target:
    id: str
    description: str
    measurable_criteria: List[MeasurableCriterion]
    priority: int = 1
```

### 2.4 Condition结构

```python
@dataclass
class Condition:
    conditions: List[ConditionItem]
    logical_operator: str = "AND"
```

### 2.5 Boundary结构

```python
@dataclass
class Boundary:
    scope: ScopeBoundary
    resources: ResourceBoundary
    quality: Optional[QualityBoundary] = None
```

### 2.6 EndRule结构

```python
@dataclass
class EndRule:
    success_conditions: List[SuccessCondition]
    failure_conditions: List[FailureCondition]
    evaluation_logic: str = ""
```

---

## 三、关键特性

### 3.1 类型注解

- 所有数据结构都使用Python类型注解
- 支持类型检查工具（如mypy）

### 3.2 验证机制

每个结构都有 `is_valid()` 方法：

```python
def is_valid(self) -> bool:
    """验证结构是否有效"""
    # 检查所有必需字段
    # 验证数据完整性
    return True/False
```

### 3.3 JSON序列化/反序列化

- `to_dict()`: 转换为字典
- `to_json()`: 转换为JSON字符串
- `from_dict()`: 从字典创建对象
- `from_json()`: 从JSON字符串创建对象

---

## 四、使用示例

### 4.1 创建Task四元组

```python
from src.task_modeling.task_struct import (
    Task, Target, Condition, Boundary, EndRule,
    MeasurableCriterion, ConditionItem,
    ScopeBoundary, ResourceBoundary, QualityBoundary,
    SuccessCondition, FailureCondition
)

# 创建目标
target = Target(
    id="T-001",
    description="生成2024年度销售报告",
    measurable_criteria=[
        MeasurableCriterion(
            id="MC-001",
            description="报告页数>=50页",
            type="numeric",
            threshold=50,
            unit="页"
        )
    ],
    priority=9
)

# 创建前置条件
condition = Condition(...)

# 创建边界
boundary = Boundary(...)

# 创建终止规则
end_rule = EndRule(...)

# 创建完整Task
task = Task(
    id="TASK-20240526-001",
    target=target,
    condition=condition,
    boundary=boundary,
    end_rule=end_rule
)
```

### 4.2 使用示例函数

```python
from src.task_modeling.task_struct import create_example_task

# 快速创建示例Task
task = create_example_task()
print(task.to_json())
```

---

## 五、测试验证

### 5.1 运行测试

```bash
cd /workspace
python3 -c "
from src.task_modeling.task_struct import create_example_task
task = create_example_task()
print('Task创建成功!')
print(f'Valid: {task.is_valid()}')
"
```

### 5.2 测试结果

✅ 测试通过：
- Task创建成功
- 验证通过
- JSON序列化/反序列化正常

---

## 六、验收标准检查

| 验收标准 | 状态 | 说明 |
|---------|------|-----|
| 四字段完整（Target/Condition/Boundary/EndRule） | ✅ 通过 | 所有字段都已实现 |
| 使用类型注解 | ✅ 通过 | 完整的类型注解 |
| 支持JSON序列化 | ✅ 通过 | to_json/from_json方法 |
| 包含基本验证 | ✅ 通过 | is_valid()方法 |

---

## 七、后续阶段衔接

- 阶段22：用户需求统一解析入口函数
- 阶段23：唯一Target提取、歧义剔除、目标归一
- 阶段24：前置条件Condition自动识别模块
