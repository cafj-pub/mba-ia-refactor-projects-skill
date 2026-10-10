import logging

from sqlalchemy.orm import joinedload

from database import db
from models import stats
from models.category import Category
from models.task import Task
from models.user import User
from utils.constants import (
    DEFAULT_PRIORITY, STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING,
)
from utils.errors import NotFoundError, ValidationError
from utils.helpers import calculate_percentage
from utils.time import utcnow
from utils.validators import (
    normalize_tags, parse_due_date, parse_int_param, require_json, validate_priority, validate_status,
    validate_title,
)

logger = logging.getLogger(__name__)


def get_task_or_404(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def _get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def _ensure_category_exists(category_id):
    if not db.session.get(Category, category_id):
        raise NotFoundError('Categoria não encontrada')


class TaskController:
    def __init__(self, notification_service):
        self._notifications = notification_service

    def list_tasks(self):
        tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
        now = utcnow()
        result = []
        for task in tasks:
            data = task.to_dict()
            data['overdue'] = task.is_overdue(now)
            data['user_name'] = task.user.name if task.user else None
            data['category_name'] = task.category.name if task.category else None
            result.append(data)
        return result

    def get_task(self, task_id):
        return get_task_or_404(task_id).to_dict(include_overdue=True)

    def create_task(self, data):
        require_json(data)
        if not data.get('title'):
            raise ValidationError('Título é obrigatório')

        task = Task(
            title=validate_title(data['title']),
            description=data.get('description', ''),
            status=validate_status(data.get('status', STATUS_PENDING)),
            priority=validate_priority(data.get('priority', DEFAULT_PRIORITY)),
            user_id=data.get('user_id'),
            category_id=data.get('category_id'),
        )
        assignee = _get_user_or_404(task.user_id) if task.user_id else None
        if task.category_id:
            _ensure_category_exists(task.category_id)
        if data.get('due_date'):
            task.due_date = parse_due_date(data['due_date'])
        if data.get('tags'):
            task.tags = normalize_tags(data['tags'])

        db.session.add(task)
        db.session.commit()
        logger.info('Task criada: %s', task.id)

        if assignee:
            self._notifications.notify_task_assigned(assignee, task)
        return task.to_dict()

    def update_task(self, task_id, data):
        task = get_task_or_404(task_id)
        require_json(data)

        if 'title' in data:
            task.title = validate_title(data['title'])
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = validate_status(data['status'])
        if 'priority' in data:
            task.priority = validate_priority(data['priority'])
        if 'user_id' in data:
            if data['user_id']:
                _get_user_or_404(data['user_id'])
            task.user_id = data['user_id']
        if 'category_id' in data:
            if data['category_id']:
                _ensure_category_exists(data['category_id'])
            task.category_id = data['category_id']
        if 'due_date' in data:
            task.due_date = parse_due_date(data['due_date']) if data['due_date'] else None
        if 'tags' in data:
            task.tags = normalize_tags(data['tags'])

        task.updated_at = utcnow()
        db.session.commit()
        logger.info('Task atualizada: %s', task.id)
        return task.to_dict()

    def delete_task(self, task_id):
        task = get_task_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        logger.info('Task deletada: %s', task_id)

    def search_tasks(self, query, status, priority, user_id):
        tasks = Task.query
        if query:
            tasks = tasks.filter(db.or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%')))
        if status:
            tasks = tasks.filter(Task.status == status)
        if priority:
            tasks = tasks.filter(Task.priority == parse_int_param(priority, 'Prioridade inválida'))
        if user_id:
            tasks = tasks.filter(Task.user_id == parse_int_param(user_id, 'user_id inválido'))
        return [task.to_dict() for task in tasks.all()]

    def task_stats(self):
        by_status = stats.count_tasks_by_status()
        total = sum(by_status.values())
        done = by_status.get(STATUS_DONE, 0)
        return {
            'total': total,
            STATUS_PENDING: by_status.get(STATUS_PENDING, 0),
            STATUS_IN_PROGRESS: by_status.get(STATUS_IN_PROGRESS, 0),
            STATUS_DONE: done,
            STATUS_CANCELLED: by_status.get(STATUS_CANCELLED, 0),
            'overdue': stats.count_overdue_tasks(utcnow()),
            'completion_rate': calculate_percentage(done, total),
        }
