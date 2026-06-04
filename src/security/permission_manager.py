"""
基础权限与数据隔离机制
基于第一性原理的AI Agent任务规划系统

核心功能：
- 用户权限管理
- 任务数据隔离
- 访问控制
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class PermissionLevel(Enum):
    """权限级别"""
    NONE = 0      # 无权限
    READ = 1      # 只读
    WRITE = 2     # 读写
    ADMIN = 3     # 管理员


@dataclass
class User:
    """用户"""
    user_id: str
    username: str
    permission_level: PermissionLevel = PermissionLevel.READ
    created_tasks: Set[str] = field(default_factory=set)


@dataclass
class TaskPermission:
    """任务权限"""
    task_id: str
    owner_id: str
    allowed_users: Set[str] = field(default_factory=set)
    is_public: bool = False


class PermissionManager:
    """
    权限管理器
    
    功能：
    - 用户权限管理
    - 任务数据隔离
    - 访问控制
    """
    
    def __init__(self):
        """初始化权限管理器"""
        self._users: Dict[str, User] = {}
        self._task_permissions: Dict[str, TaskPermission] = {}
    
    def create_user(self, user_id: str, username: str, level: PermissionLevel = PermissionLevel.READ) -> User:
        """创建用户"""
        user = User(user_id=user_id, username=username, permission_level=level)
        self._users[user_id] = user
        return user
    
    def check_permission(self, user_id: str, task_id: str) -> bool:
        """检查用户是否有权限访问任务"""
        if user_id not in self._users:
            return False
        
        user = self._users[user_id]
        
        # 管理员拥有所有权限
        if user.permission_level == PermissionLevel.ADMIN:
            return True
        
        # 检查任务权限
        if task_id in self._task_permissions:
            task_perm = self._task_permissions[task_id]
            if task_perm.is_public:
                return True
            if user_id == task_perm.owner_id:
                return True
            if user_id in task_perm.allowed_users:
                return True
        
        return False
    
    def create_task_permission(self, task_id: str, owner_id: str, is_public: bool = False) -> TaskPermission:
        """创建任务权限"""
        perm = TaskPermission(task_id=task_id, owner_id=owner_id, is_public=is_public)
        self._task_permissions[task_id] = perm
        
        # 记录到用户的创建列表
        if owner_id in self._users:
            self._users[owner_id].created_tasks.add(task_id)
        
        return perm
    
    def share_task(self, task_id: str, owner_id: str, target_user_id: str) -> bool:
        """分享任务给其他用户"""
        if task_id not in self._task_permissions:
            return False
        
        task_perm = self._task_permissions[task_id]
        if task_perm.owner_id != owner_id:
            return False
        
        task_perm.allowed_users.add(target_user_id)
        return True
