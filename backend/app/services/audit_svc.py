"""
Audit Service

Ghi lại mọi thay đổi quan trọng trong hệ thống.
"""

from sqlalchemy.orm import Session
from app.db.models.audit import AuditLog
from typing import Optional, Any
import json


def log_action(
        db: Session,
        user_id: str,
        emp_code: str,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        old_data: Optional[Any] = None,
        new_data: Optional[Any] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
):
    """
    Ghi audit log.

    Args:
        db: Database session
        user_id: User UUID
        emp_code: Employee code
        action: CREATE, UPDATE, DELETE, ALLOCATE, MANUAL_ADJUST, IMPORT
        entity_type: EVENT, FLIGHT, VEHICLE, REGISTRATION, etc.
        entity_id: UUID của entity
        old_data: Dữ liệu trước khi thay đổi
        new_data: Dữ liệu sau khi thay đổi
        reason: Lý do thay đổi
        ip_address: IP address
        user_agent: User agent
    """
    # Convert data to JSON-serializable format
    if old_data is not None and not isinstance(old_data, (dict, list, str, int, float, bool, type(None))):
        old_data = str(old_data)

    if new_data is not None and not isinstance(new_data, (dict, list, str, int, float, bool, type(None))):
        new_data = str(new_data)

    audit_log = AuditLog(
        user_id=user_id,
        emp_code=emp_code,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_data=old_data,
        new_data=new_data,
        reason=reason,
        ip_address=ip_address,
        user_agent=user_agent
    )

    db.add(audit_log)
    db.commit()

    print(f"[AUDIT LOG] {emp_code} {action} {entity_type} {entity_id or ''}")


def get_entity_audit_logs(
        db: Session,
        entity_type: str,
        entity_id: str,
        limit: int = 50
):
    """
    Lấy audit logs của một entity.

    Args:
        db: Database session
        entity_type: Loại entity
        entity_id: UUID của entity
        limit: Số lượng logs tối đa

    Returns:
        List of audit logs
    """
    logs = db.query(AuditLog).filter(
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(AuditLog.created_at.desc()).limit(limit).all()

    return logs


def get_user_audit_logs(
        db: Session,
        user_id: str,
        limit: int = 50
):
    """
    Lấy audit logs của một user.

    Args:
        db: Database session
        user_id: User UUID
        limit: Số lượng logs tối đa

    Returns:
        List of audit logs
    """
    logs = db.query(AuditLog).filter(
        AuditLog.user_id == user_id
    ).order_by(AuditLog.created_at.desc()).limit(limit).all()

    return logs
