"""Constantes de domínio do Task Manager."""

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
VALID_STATUSES = [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED]
# Tasks nesses status nunca ficam atrasadas.
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
# Prioridades <= este valor contam como "alta prioridade" nos relatórios.
HIGH_PRIORITY_THRESHOLD = 2
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
VALID_ROLES = [ROLE_USER, ROLE_ADMIN, ROLE_MANAGER]
DEFAULT_ROLE = ROLE_USER
MIN_PASSWORD_LENGTH = 4

DEFAULT_COLOR = '#000000'

RECENT_ACTIVITY_DAYS = 7
DATE_FORMAT = '%Y-%m-%d'
