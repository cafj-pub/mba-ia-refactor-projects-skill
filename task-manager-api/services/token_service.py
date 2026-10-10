from itsdangerous import URLSafeTimedSerializer


class TokenService:
    """Emite tokens de autenticação assinados com a SECRET_KEY da aplicação."""

    def __init__(self, secret_key):
        self._serializer = URLSafeTimedSerializer(secret_key, salt='auth-token')

    def issue(self, user):
        return self._serializer.dumps({'user_id': user.id, 'role': user.role})
