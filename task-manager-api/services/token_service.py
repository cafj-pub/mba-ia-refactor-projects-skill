from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from utils.errors import UnauthorizedError

INVALID_TOKEN_MESSAGE = 'Token de autenticação ausente ou inválido'


class TokenService:
    """Emite e verifica tokens de autenticação assinados com a SECRET_KEY da aplicação."""

    def __init__(self, secret_key, max_age_seconds):
        self._serializer = URLSafeTimedSerializer(secret_key, salt='auth-token')
        self._max_age = max_age_seconds

    def issue(self, user):
        # Só o id: perfil e status são sempre recarregados do banco na verificação.
        return self._serializer.dumps({'user_id': user.id})

    def verify(self, token):
        """Retorna o user_id do token ou lança UnauthorizedError (assinatura inválida ou expirada)."""
        try:
            return self._serializer.loads(token, max_age=self._max_age)['user_id']
        except (BadSignature, SignatureExpired, KeyError, TypeError):
            raise UnauthorizedError(INVALID_TOKEN_MESSAGE)
