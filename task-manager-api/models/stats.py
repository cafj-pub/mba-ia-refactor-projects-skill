"""Consultas agregadas sobre tasks (uma query por agregação, sem N+1)."""
from sqlalchemy import case, func

from database import db
from models.task import Task
from models.user import User
from utils.constants import CLOSED_STATUSES, STATUS_DONE


def count_tasks_by_status():
    return dict(db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all())


def count_tasks_by_priority():
    return dict(db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all())


def _overdue_filter(now):
    return Task.due_date.isnot(None), Task.due_date < now, Task.status.notin_(CLOSED_STATUSES)


def overdue_tasks(now):
    return Task.query.filter(*_overdue_filter(now)).order_by(Task.id).all()


def count_overdue_tasks(now):
    return Task.query.filter(*_overdue_filter(now)).count()


def count_tasks_created_since(since):
    return Task.query.filter(Task.created_at >= since).count()


def count_tasks_completed_since(since):
    return Task.query.filter(Task.status == STATUS_DONE, Task.updated_at >= since).count()


def count_tasks_by_user():
    return dict(db.session.query(Task.user_id, func.count(Task.id)).group_by(Task.user_id).all())


def count_tasks_by_category():
    return dict(db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all())


def completion_by_user():
    """Lista (user_id, user_name, total_tasks, completed_tasks) para todos os usuários."""
    completed = func.coalesce(func.sum(case((Task.status == STATUS_DONE, 1), else_=0)), 0)
    return (
        db.session.query(User.id, User.name, func.count(Task.id), completed)
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id, User.name)
        .order_by(User.id)
        .all()
    )
