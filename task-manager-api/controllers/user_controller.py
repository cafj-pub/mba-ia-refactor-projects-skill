import logging

from database import db
from models import stats
from models.task import Task
from models.user import User
from utils.constants import DEFAULT_ROLE, MIN_PASSWORD_LENGTH
from utils.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from utils.validators import require_json, validate_email, validate_password, validate_role

logger = logging.getLogger(__name__)


def get_user_or_404(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def _ensure_email_available(email, current_user_id=None):
    existing = User.query.filter_by(email=email).first()
    if existing and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')


class UserController:
    def __init__(self, token_service):
        self._tokens = token_service

    def list_users(self):
        task_counts = stats.count_tasks_by_user()
        return [
            {**user.to_dict(), 'task_count': task_counts.get(user.id, 0)}
            for user in User.query.order_by(User.id).all()
        ]

    def get_user(self, user_id):
        user = get_user_or_404(user_id)
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in Task.query.filter_by(user_id=user_id).all()]
        return data

    def create_user(self, data):
        require_json(data)
        name, email, password = data.get('name'), data.get('email'), data.get('password')
        role = data.get('role', DEFAULT_ROLE)

        if not name:
            raise ValidationError('Nome é obrigatório')
        if not email:
            raise ValidationError('Email é obrigatório')
        if not password:
            raise ValidationError('Senha é obrigatória')
        validate_email(email)
        validate_password(password, f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
        _ensure_email_available(email)
        validate_role(role)

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        logger.info('Usuário criado: %s', user.id)
        return user.to_dict()

    def update_user(self, user_id, data):
        user = get_user_or_404(user_id)
        require_json(data)

        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            validate_email(data['email'])
            _ensure_email_available(data['email'], current_user_id=user_id)
            user.email = data['email']
        if 'password' in data:
            user.set_password(validate_password(data['password'], 'Senha muito curta'))
        if 'role' in data:
            user.role = validate_role(data['role'])
        if 'active' in data:
            user.active = data['active']

        db.session.commit()
        return user.to_dict()

    def delete_user(self, user_id):
        user = get_user_or_404(user_id)
        # Tasks do usuário são removidas em lote, na mesma transação.
        Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        db.session.delete(user)
        db.session.commit()
        logger.info('Usuário deletado: %s', user_id)

    def get_user_tasks(self, user_id):
        get_user_or_404(user_id)
        return [task.to_summary_dict() for task in Task.query.filter_by(user_id=user_id).all()]

    def login(self, data):
        require_json(data)
        email, password = data.get('email'), data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')

        db.session.commit()  # persiste eventual migração do hash legado
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': self._tokens.issue(user),
        }
