"""
SQLAlchemy models for Role-Based Access Control (RBAC).
Includes Role, Permission, RolePermission (many-to-many), and UserRole models.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.db import Base


class Role(Base):
    """User roles (e.g., admin, user, viewer, manager)."""
    __tablename__ = 'roles'

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    role_permissions = relationship('RolePermission', back_populates='role', cascade='all, delete-orphan')
    user_roles = relationship('UserRole', back_populates='role', cascade='all, delete-orphan')


class Permission(Base):
    """System permissions (e.g., read:users, write:users, delete:posts)."""
    __tablename__ = 'permissions'

    permission_id = Column(Integer, primary_key=True, autoincrement=True)
    permission_name = Column(String, unique=True, nullable=False, index=True)
    resource = Column(String, nullable=True)  # e.g., 'users', 'posts', 'settings'
    action = Column(String, nullable=True)  # e.g., 'read', 'write', 'delete'
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    role_permissions = relationship('RolePermission', back_populates='permission', cascade='all, delete-orphan')


class RolePermission(Base):
    """Many-to-many relationship between roles and permissions."""
    __tablename__ = 'role_permissions'

    role_id = Column(Integer, ForeignKey('roles.role_id', ondelete='CASCADE'), primary_key=True)
    permission_id = Column(Integer, ForeignKey('permissions.permission_id', ondelete='CASCADE'), primary_key=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    role = relationship('Role', back_populates='role_permissions')
    permission = relationship('Permission', back_populates='role_permissions')


class UserRole(Base):
    """Many-to-many relationship between users and roles."""
    __tablename__ = 'user_roles'

    user_id = Column(Integer, ForeignKey('user_profiles.user_id', ondelete='CASCADE'), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.role_id', ondelete='CASCADE'), primary_key=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(Integer, nullable=True)  # ID of admin who assigned the role

    # Relationships
    role = relationship('Role', back_populates='user_roles')
    # Note: UserProfile relationship is defined in users/models.py to avoid circular imports
