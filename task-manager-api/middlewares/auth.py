import functools

from flask import g, request

from services.token_service import INVALID_TOKEN_MESSAGE
from utils.errors import ForbiddenError, UnauthorizedError


class Auth:
    """Autenticação via `Authorization: Bearer <token>`.

    `load_user(user_id)` recarrega o usuário do banco, para que perfil e status
    reflitam o estado atual e não o momento em que o token foi emitido.
    """

    def __init__(self, token_service, load_user):
        self._tokens = token_service
        self._load_user = load_user

    def _bearer_token(self):
        scheme, _, token = request.headers.get('Authorization', '').partition(' ')
        return token.strip() if scheme.lower() == 'bearer' else ''

    def _authenticate(self):
        token = self._bearer_token()
        if not token:
            raise UnauthorizedError(INVALID_TOKEN_MESSAGE)
        user = self._load_user(self._tokens.verify(token))
        if not user or not user.active:
            raise UnauthorizedError(INVALID_TOKEN_MESSAGE)
        g.current_user = user
        return user

    def optional_user(self):
        """Usuário autenticado, ou None se a requisição não enviou token. Token inválido → 401."""
        return self._authenticate() if self._bearer_token() else None

    def require_auth(self, view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            self._authenticate()
            return view(*args, **kwargs)
        return wrapper

    def require_admin(self, view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            if not self._authenticate().is_admin():
                raise ForbiddenError('Acesso negado')
            return view(*args, **kwargs)
        return wrapper
