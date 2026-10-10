from datetime import timedelta

from models import stats
from models.category import Category
from models.task import Task
from models.user import User
from controllers.user_controller import get_user_or_404
from utils.constants import (
    HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, STATUS_CANCELLED, STATUS_DONE,
    STATUS_IN_PROGRESS, STATUS_PENDING, VALID_STATUSES,
)
from utils.helpers import calculate_percentage
from utils.time import utcnow


class ReportController:
    def summary(self):
        now = utcnow()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = stats.count_tasks_by_status()
        by_priority = stats.count_tasks_by_priority()
        overdue = stats.overdue_tasks(now)

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': sum(by_status.values()),
                'total_users': User.query.count(),
                'total_categories': Category.query.count(),
            },
            'tasks_by_status': {status: by_status.get(status, 0) for status in VALID_STATUSES},
            'tasks_by_priority': {label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()},
            'overdue': {
                'count': len(overdue),
                'tasks': [
                    {
                        'id': task.id,
                        'title': task.title,
                        'due_date': str(task.due_date),
                        'days_overdue': (now - task.due_date).days,
                    }
                    for task in overdue
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': stats.count_tasks_created_since(since),
                'tasks_completed_last_7_days': stats.count_tasks_completed_since(since),
            },
            'user_productivity': [
                {
                    'user_id': user_id,
                    'user_name': user_name,
                    'total_tasks': total,
                    'completed_tasks': completed,
                    'completion_rate': calculate_percentage(completed, total),
                }
                for user_id, user_name, total, completed in stats.completion_by_user()
            ],
        }

    def user_report(self, user_id):
        user = get_user_or_404(user_id)
        tasks = Task.query.filter_by(user_id=user_id).all()
        now = utcnow()

        by_status = {status: 0 for status in VALID_STATUSES}
        for task in tasks:
            if task.status in by_status:
                by_status[task.status] += 1

        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': len(tasks),
                'done': by_status[STATUS_DONE],
                'pending': by_status[STATUS_PENDING],
                'in_progress': by_status[STATUS_IN_PROGRESS],
                'cancelled': by_status[STATUS_CANCELLED],
                'overdue': sum(1 for task in tasks if task.is_overdue(now)),
                'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
                'completion_rate': calculate_percentage(by_status[STATUS_DONE], len(tasks)),
            },
        }
