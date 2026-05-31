
# 第5阶段交付物：Task 四元组规范文档

---

## 一、四元组结构总览

根据公理1：**所有人类任务，都是「明确目标 + 有限前置条件 + 固定依赖关系 + 可终止步骤序列」，不存在无限任务、无逻辑任务。**

```typescript
interface Task {
  target: Target;          // 唯一明确目标
  condition: Condition;    // 前置条件集合
  boundary: Boundary;      // 边界约束集合
  endRule: EndRule;        // 终止判定规则
}
```

---

## 二、Target（目标）字段规范

### 2.1 字段定义

| 属性 | 规范 |
|-----|------|
| **唯一要求** | 必须唯一、明确、可衡量 |
| **禁止内容** | 多目标、模糊表述、歧义内容 |
| **格式要求** | 结构化、机器可解析 |

### 2.2 字段结构

```typescript
interface Target {
  id: string;                          // 目标唯一标识
  description: string;                 // 目标描述（人类可读）
  measurableCriteria: MeasurableCriterion[];  // 可衡量标准列表
  priority: number;                    // 优先级（1-10，10最高）
}

interface MeasurableCriterion {
  id: string;                          // 标准唯一标识
  description: string;                 // 标准描述
  type: 'boolean' | 'numeric' | 'qualitative';  // 标准类型
  threshold: any;                      // 判定阈值
  unit?: string;                       // 单位（可选）
}
```

### 2.3 判定标准（可机器判定）

| 判定项 | 通过条件 | 不通过示例 |
|-------|---------|----------|
| 唯一性 | 仅有一个核心目标 | ❌ "写报告和做PPT" |
| 明确性 | 无模糊词汇（"大概"、"尽量"、"可能"） | ❌ "尽量写好报告" |
| 可衡量性 | 有具体量化或明确质化标准 | ❌ "做好项目" |

### 2.4 示例

#### ✅ 合法示例

```json
{
  "target": {
    "id": "T-001",
    "description": "完成2024年度销售报告",
    "measurableCriteria": [
      {
        "id": "MC-001",
        "description": "报告页数≥50页",
        "type": "numeric",
        "threshold": 50,
        "unit": "页"
      },
      {
        "id": "MC-002",
        "description": "包含完整4个季度数据",
        "type": "boolean",
        "threshold": true
      }
    ],
    "priority": 8
  }
}
```

#### ❌ 非法示例

```json
{
  "target": {
    "id": "T-002",
    "description": "尽量做好项目，可能还要做PPT",  // ❌ 多目标、模糊
    "measurableCriteria": [],  // ❌ 无可衡量标准
    "priority": 5
  }
}
```

---

## 三、Condition（前置条件）字段规范

### 3.1 字段定义

| 属性 | 规范 |
|-----|------|
| **定义** | 任务启动前必须满足的条件 |
| **要求** | 每个条件可机器判定 True/False |
| **格式** | 结构化条件列表 |

### 3.2 字段结构

```typescript
interface Condition {
  conditions: ConditionItem[];        // 前置条件列表
  logicalOperator: 'AND' | 'OR';      // 条件间逻辑关系
}

interface ConditionItem {
  id: string;                         // 条件唯一标识
  description: string;                // 条件描述
  type: 'existence' | 'value' | 'state';  // 条件类型
  checkRule: string;                  // 机器可执行的检查规则
  required: boolean;                  // 是否必须满足
}
```

### 3.3 判定标准

| 判定项 | 通过条件 |
|-------|---------|
| 可判定性 | 每个条件有明确的 True/False 判定规则 |
| 完整性 | 所有必要前置条件都已列出 |
| 可执行性 | checkRule 可被机器自动执行 |

### 3.4 示例

#### ✅ 合法示例

```json
{
  "condition": {
    "conditions": [
      {
        "id": "C-001",
        "description": "Q1销售数据文件存在",
        "type": "existence",
        "checkRule": "file_exists('/data/q1_sales.csv')",
        "required": true
      },
      {
        "id": "C-002",
        "description": "数据库连接正常",
        "type": "state",
        "checkRule": "db_ping() == true",
        "required": true
      }
    ],
    "logicalOperator": "AND"
  }
}
```

---

## 四、Boundary（边界约束）字段规范

### 4.1 字段定义

| 属性 | 规范 |
|-----|------|
| **定义** | 任务执行的边界限制 |
| **内容** | 范围边界、资源约束、质量约束 |
| **要求** | 所有约束可量化、可验证 |

### 4.2 字段结构

```typescript
interface Boundary {
  scope: ScopeBoundary;               // 范围边界
  resources: ResourceBoundary;        // 资源约束
  quality: QualityBoundary;           // 质量约束
}

interface ScopeBoundary {
  inclusions: string[];               // 包含范围
  exclusions: string[];               // 排除范围
}

interface ResourceBoundary {
  maxTimeSeconds: number;             // 最大时间（秒）
  maxCost: number;                    // 最大成本
  maxIterations: number;              // 最大迭代次数
}

interface QualityBoundary {
  minAccuracy?: number;               // 最低准确率（0-1）
  maxErrorRate?: number;              // 最高错误率（0-1）
  otherConstraints?: string[];        // 其他质量约束
}
```

### 4.3 判定标准

| 判定项 | 通过条件 |
|-------|---------|
| 明确性 | 范围有明确的包含/排除定义 |
| 可量化 | 资源约束有具体数值 |
| 可验证 | 质量约束有可验证标准 |

### 4.4 示例

#### ✅ 合法示例

```json
{
  "boundary": {
    "scope": {
      "inclusions": ["2024年度销售数据", "中国区业务"],
      "exclusions": ["海外业务", "非销售数据"]
    },
    "resources": {
      "maxTimeSeconds": 7200,
      "maxCost": 1000,
      "maxIterations": 10
    },
    "quality": {
      "minAccuracy": 0.95,
      "maxErrorRate": 0.01
    }
  }
}
```

---

## 五、EndRule（终止规则）字段规范

### 5.1 字段定义

| 属性 | 规范 |
|-----|------|
| **定义** | 任务终止的明确判定规则 |
| **要求** | 100% 机器可自动判定 True/False |
| **禁止** | 模糊表述、人工判定 |

### 5.2 字段结构

```typescript
interface EndRule {
  successConditions: SuccessCondition[];  // 成功终止条件
  failureConditions: FailureCondition[];  // 失败终止条件
  evaluationLogic: string;                // 判定逻辑表达式
}

interface SuccessCondition {
  id: string;                         // 条件唯一标识
  description: string;                // 条件描述
  checkRule: string;                  // 机器可执行的检查规则
}

interface FailureCondition {
  id: string;                         // 条件唯一标识
  description: string;                // 条件描述
  checkRule: string;                  // 机器可执行的检查规则
  priority: number;                   // 优先级（优先触发）
}
```

### 5.3 判定标准（核心：必须机器可判定）

| 判定项 | 通过条件 |
|-------|---------|
| 无歧义 | 没有"合适"、"满意"等主观词汇 |
| 可执行 | checkRule 可直接被程序执行 |
| 完整性 | 成功和失败条件都明确 |

### 5.4 示例

#### ✅ 合法示例

```json
{
  "endRule": {
    "successConditions": [
      {
        "id": "SC-001",
        "description": "报告文件已生成",
        "checkRule": "file_exists('/output/annual_report.pdf') == true"
      },
      {
        "id": "SC-002",
        "description": "所有可衡量标准满足",
        "checkRule": "all_measurable_criteria_met() == true"
      }
    ],
    "failureConditions": [
      {
        "id": "FC-001",
        "description": "超时",
        "checkRule": "elapsed_time() &gt; 7200",
        "priority": 1
      },
      {
        "id": "FC-002",
        "description": "连续错误超过5次",
        "checkRule": "consecutive_errors() &gt;= 5",
        "priority": 2
      }
    ],
    "evaluationLogic": "success: (SC-001 AND SC-002); failure: (FC-001 OR FC-002)"
  }
}
```

---

## 六、完整 Task 四元组示例

### 6.1 完整示例

```json
{
  "target": {
    "id": "T-REPORT-2024",
    "description": "生成2024年度中国区销售分析报告",
    "measurableCriteria": [
      {
        "id": "MC-001",
        "description": "报告页数≥50页",
        "type": "numeric",
        "threshold": 50,
        "unit": "页"
      },
      {
        "id": "MC-002",
        "description": "包含4个季度完整数据",
        "type": "boolean",
        "threshold": true
      },
      {
        "id": "MC-003",
        "description": "包含至少10张图表",
        "type": "numeric",
        "threshold": 10,
        "unit": "张"
      }
    ],
    "priority": 9
  },
  "condition": {
    "conditions": [
      {
        "id": "C-001",
        "description": "Q1销售数据存在",
        "type": "existence",
        "checkRule": "file_exists('/data/2024_q1.csv')",
        "required": true
      },
      {
        "id": "C-002",
        "description": "Q2销售数据存在",
        "type": "existence",
        "checkRule": "file_exists('/data/2024_q2.csv')",
        "required": true
      },
      {
        "id": "C-003",
        "description": "Q3销售数据存在",
        "type": "existence",
        "checkRule": "file_exists('/data/2024_q3.csv')",
        "required": true
      },
      {
        "id": "C-004",
        "description": "Q4销售数据存在",
        "type": "existence",
        "checkRule": "file_exists('/data/2024_q4.csv')",
        "required": true
      }
    ],
    "logicalOperator": "AND"
  },
  "boundary": {
    "scope": {
      "inclusions": ["2024年度", "中国区", "销售数据"],
      "exclusions": ["海外业务", "非销售数据", "2023年及之前数据"]
    },
    "resources": {
      "maxTimeSeconds": 7200,
      "maxCost": 500,
      "maxIterations": 5
    },
    "quality": {
      "minAccuracy": 0.98,
      "maxErrorRate": 0.005
    }
  },
  "endRule": {
    "successConditions": [
      {
        "id": "SC-001",
        "description": "报告PDF文件已生成",
        "checkRule": "file_exists('/output/2024_sales_report.pdf') == true"
      },
      {
        "id": "SC-002",
        "description": "所有可衡量标准满足",
        "checkRule": "all_measurable_criteria_met() == true"
      },
      {
        "id": "SC-003",
        "description": "报告文件大小&gt;1MB",
        "checkRule": "file_size('/output/2024_sales_report.pdf') &gt; 1048576"
      }
    ],
    "failureConditions": [
      {
        "id": "FC-001",
        "description": "执行超时",
        "checkRule": "elapsed_time() &gt; 7200",
        "priority": 1
      },
      {
        "id": "FC-002",
        "description": "超过最大迭代次数",
        "checkRule": "iteration_count() &gt;= 5",
        "priority": 2
      },
      {
        "id": "FC-003",
        "description": "连续错误超过3次",
        "checkRule": "consecutive_errors() &gt;= 3",
        "priority": 3
      }
    ],
    "evaluationLogic": "success: (SC-001 AND SC-002 AND SC-003); failure: (FC-001 OR FC-002 OR FC-003)"
  }
}
```

---

## 七、四元组合法性校验规则

### 7.1 校验检查列表

| 检查项 | 检查内容 |
|-------|---------|
| Target | 唯一、明确、可衡量 |
| Condition | 每个条件可机器判定 |
| Boundary | 范围明确、资源可量化 |
| EndRule | 100% 机器可自动判定 |

### 7.2 校验通过判定

所有检查项都通过 → 四元组合法，可以进入下一阶段

---

## 八、验收标准自检

| 验收标准项 | 完成状态 |
|-----------|---------|
| Target 可机器结构化判定 | ✅ 已完成 |
| Condition 可机器结构化判定 | ✅ 已完成 |
| Boundary 可机器结构化判定 | ✅ 已完成 |
| EndRule 可机器结构化判定 | ✅ 已完成 |

---

## 九、备注

本规范基于公理1编制，确保Task四元组的每个字段都可机器结构化判定，从根本上解决目标无定义、边界无约束的问题（RC-001、RC-002）。

