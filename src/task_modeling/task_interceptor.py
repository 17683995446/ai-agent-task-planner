"""
任务异常拦截与标准化拒绝反馈模块
基于第一性原理的AI Agent任务规划系统
"""

from typing import Optional, Dict, Any, List
from enum import Enum


class TaskRejectionLevel(Enum):
    """任务拒绝级别"""
    PASS = "pass"              # 通过，可进入下游
    WARNING = "warning"        # 警告，有小问题但可处理
    REJECTED = "rejected"      # 拒绝，非法任务禁止进入下游


class TaskRejectionReason(Enum):
    """任务拒绝原因分类"""
    MISSING_FIELD = "missing_field"           # 缺少必要字段
    INVALID_FORMAT = "invalid_format"         # 格式无效
    LOGIC_ERROR = "logic_error"              # 逻辑错误
    SEMANTIC_ERROR = "semantic_error"        # 语义错误
    RESOURCE_EXCEEDED = "resource_exceeded"  # 超出资源限制
    UNKNOWN_ERROR = "unknown_error"          # 未知错误


class TaskRejectionError:
    """任务拒绝错误详情"""
    
    def __init__(
        self,
        reason: TaskRejectionReason,
        field: str,
        message: str,
        severity: str = "error"
    ):
        self.reason = reason
        self.field = field
        self.message = message
        self.severity = severity  # "error", "warning", "info"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reason": self.reason.value,
            "field": self.field,
            "message": self.message,
            "severity": self.severity
        }


class TaskRejectionResponse:
    """任务拒绝响应（标准化反馈）"""
    
    def __init__(
        self,
        level: TaskRejectionLevel,
        errors: List[TaskRejectionError],
        suggestions: List[str],
        raw_errors: Optional[List[str]] = None
    ):
        self.level = level
        self.errors = errors
        self.suggestions = suggestions
        self.raw_errors = raw_errors or []
        self.is_allowed = level != TaskRejectionLevel.REJECTED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.is_allowed,
            "level": self.level.value,
            "error_count": len(self.errors),
            "errors": [e.to_dict() for e in self.errors],
            "suggestions": self.suggestions,
            "summary": self._generate_summary()
        }
    
    def _generate_summary(self) -> str:
        """生成错误摘要"""
        if self.level == TaskRejectionLevel.PASS:
            return "任务校验通过"
        elif self.level == TaskRejectionLevel.WARNING:
            return f"任务存在{len(self.errors)}个警告，但仍可进入下游处理"
        else:
            error_types = {}
            for err in self.errors:
                if err.reason not in error_types:
                    error_types[err.reason] = 0
                error_types[err.reason] += 1
            
            type_summary = ", ".join([
                f"{reason.value}: {count}个"
                for reason, count in error_types.items()
            ])
            return f"任务被拒绝，共{len(self.errors)}个错误（{type_summary}）"
    
    def to_user_message(self) -> str:
        """生成用户友好的错误消息"""
        lines = []
        
        if self.level == TaskRejectionLevel.PASS:
            lines.append("✅ 任务校验通过，可以继续执行。")
            return lines[0]
        
        lines.append(f"❌ 任务校验失败，共发现{len(self.errors)}个问题：\n")
        
        # 按字段分组显示错误
        errors_by_field = {}
        for err in self.errors:
            if err.field not in errors_by_field:
                errors_by_field[err.field] = []
            errors_by_field[err.field].append(err)
        
        for field, field_errors in errors_by_field.items():
            lines.append(f"📌 【{field}】")
            for idx, err in enumerate(field_errors, 1):
                severity_icon = "🔴" if err.severity == "error" else "🟡"
                lines.append(f"   {severity_icon} {idx}. {err.message}")
            lines.append("")
        
        # 添加建议
        if self.suggestions:
            lines.append("💡 修复建议：")
            for idx, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"   {idx}. {suggestion}")
        
        if self.level == TaskRejectionLevel.REJECTED:
            lines.append("\n🚫 该任务被拒绝，无法进入下游规划流程。")
        elif self.level == TaskRejectionLevel.WARNING:
            lines.append("\n⚠️ 该任务存在警告，但已通过初步校验。")
        
        return "\n".join(lines)


class TaskInterceptor:
    """
    任务拦截器
    功能：对非法任务进行拦截，生成标准化的拒绝反馈
    """
    
    # 错误级别阈值
    MAX_WARNINGS = 5          # 最多允许的警告数
    CRITICAL_FIELDS = ["target", "condition", "boundary", "end_rule"]  # 关键字段
    
    def __init__(self):
        """初始化任务拦截器"""
        pass
    
    def intercept(
        self,
        validation_errors: List[str],
        task_id: Optional[str] = None
    ) -> TaskRejectionResponse:
        """
        拦截非法任务并生成标准化反馈
        
        Args:
            validation_errors: 校验错误列表
            task_id: 任务ID（可选）
            
        Returns:
            TaskRejectionResponse: 标准化的拒绝响应
        """
        if not validation_errors:
            return TaskRejectionResponse(
                level=TaskRejectionLevel.PASS,
                errors=[],
                suggestions=[]
            )
        
        # 解析错误
        parsed_errors = self._parse_errors(validation_errors)
        
        # 判断拒绝级别
        level = self._determine_rejection_level(parsed_errors)
        
        # 生成建议
        suggestions = self._generate_suggestions(parsed_errors)
        
        return TaskRejectionResponse(
            level=level,
            errors=parsed_errors,
            suggestions=suggestions,
            raw_errors=validation_errors
        )
    
    def _parse_errors(self, errors: List[str]) -> List[TaskRejectionError]:
        """
        解析错误列表
        
        Args:
            errors: 原始错误字符串列表
            
        Returns:
            List[TaskRejectionError]: 解析后的错误对象列表
        """
        parsed = []
        
        for error in errors:
            # 解析错误原因
            reason = self._classify_error(error)
            
            # 解析错误字段
            field = self._extract_field(error)
            
            # 创建错误对象
            parsed.append(TaskRejectionError(
                reason=reason,
                field=field,
                message=error,
                severity=self._determine_severity(error, reason)
            ))
        
        return parsed
    
    def _classify_error(self, error: str) -> TaskRejectionReason:
        """分类错误原因"""
        error_lower = error.lower()
        
        if "不能为空" in error or "缺少" in error or "至少需要" in error:
            return TaskRejectionReason.MISSING_FIELD
        
        if "无效" in error or "无效" in error_lower:
            return TaskRejectionReason.INVALID_FORMAT
        
        if "必须" in error or "应该" in error:
            return TaskRejectionReason.LOGIC_ERROR
        
        if "类型" in error or "格式" in error:
            return TaskRejectionReason.SEMANTIC_ERROR
        
        if "超出" in error or "超过" in error or "不能为负" in error:
            return TaskRejectionReason.RESOURCE_EXCEEDED
        
        return TaskRejectionReason.UNKNOWN_ERROR
    
    def _extract_field(self, error: str) -> str:
        """提取错误字段"""
        field_keywords = ["Target", "Condition", "Boundary", "EndRule", "任务"]
        
        for keyword in field_keywords:
            if keyword in error:
                return keyword
        
        # 尝试提取中文描述的字段
        import re
        match = re.search(r'【([^】]+)】', error)
        if match:
            return match.group(1)
        
        return "general"
    
    def _determine_severity(self, error: str, reason: TaskRejectionReason) -> str:
        """判断错误严重程度"""
        # 缺少关键字段为error
        if reason == TaskRejectionReason.MISSING_FIELD:
            if "target" in error.lower() or "目标" in error:
                return "error"
            return "error"
        
        # 资源超出为warning
        if reason == TaskRejectionReason.RESOURCE_EXCEEDED:
            return "warning"
        
        return "error"
    
    def _determine_rejection_level(
        self,
        errors: List[TaskRejectionError]
    ) -> TaskRejectionLevel:
        """判断拒绝级别"""
        # 没有错误
        if not errors:
            return TaskRejectionLevel.PASS
        
        # 检查关键字段是否缺失
        critical_errors = [
            e for e in errors
            if e.field in self.CRITICAL_FIELDS
            and e.reason == TaskRejectionReason.MISSING_FIELD
        ]
        
        if critical_errors:
            return TaskRejectionLevel.REJECTED
        
        # 检查是否有过多警告
        warnings = [e for e in errors if e.severity == "warning"]
        if len(warnings) > self.MAX_WARNINGS:
            return TaskRejectionLevel.REJECTED
        
        # 有错误但非关键字段
        if errors:
            return TaskRejectionLevel.WARNING
        
        return TaskRejectionLevel.PASS
    
    def _generate_suggestions(
        self,
        errors: List[TaskRejectionError]
    ) -> List[str]:
        """生成修复建议"""
        suggestions = []
        
        # 按原因分组
        reasons = {}
        for err in errors:
            if err.reason not in reasons:
                reasons[err.reason] = []
            reasons[err.reason].append(err)
        
        # 为每种错误类型生成建议
        if TaskRejectionReason.MISSING_FIELD in reasons:
            suggestions.append("请补充所有必要的信息字段后再提交任务。")
        
        if TaskRejectionReason.INVALID_FORMAT in reasons:
            suggestions.append("请检查输入格式是否符合要求。")
        
        if TaskRejectionReason.RESOURCE_EXCEEDED in reasons:
            suggestions.append("请调整资源约束到合理范围内。")
        
        if len(errors) > 5:
            suggestions.append("错误较多，建议重新整理任务描述。")
        
        # 通用建议
        if not suggestions:
            suggestions.append("请根据上述错误信息进行修改后重试。")
        
        return suggestions


# 便捷函数
def intercept_task(
    validation_errors: List[str],
    task_id: Optional[str] = None
) -> TaskRejectionResponse:
    """
    便捷函数：拦截任务并生成标准化反馈
    
    Args:
        validation_errors: 校验错误列表
        task_id: 任务ID（可选）
        
    Returns:
        TaskRejectionResponse: 标准化的拒绝响应
    """
    interceptor = TaskInterceptor()
    return interceptor.intercept(validation_errors, task_id)
