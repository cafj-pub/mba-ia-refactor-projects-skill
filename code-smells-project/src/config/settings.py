import os
import secrets

API_VERSION = "1.0.0"


def _env_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    """Configuração da aplicação lida de variáveis de ambiente, com defaults seguros."""

    def __init__(self, env=None):
        env = os.environ if env is None else env
        # Sem SECRET_KEY definida, gera uma chave aleatória por processo (adequado só para dev).
        self.secret_key = env.get("SECRET_KEY") or secrets.token_hex(32)
        self.debug = _env_bool(env.get("FLASK_DEBUG"))
        self.host = env.get("HOST", "127.0.0.1")
        self.port = int(env.get("PORT", "5000"))
        self.database_path = env.get("DATABASE_PATH", "loja.db")
        self.cors_origins = env.get("CORS_ORIGINS", "*")
        # Token exigido por /admin/reset-db; vazio = endpoint desabilitado.
        self.admin_token = env.get("ADMIN_TOKEN", "")
        # Senha do admin criado pelo seed; vazia = senha aleatória.
        self.seed_admin_password = env.get("SEED_ADMIN_PASSWORD", "")
        self.environment = env.get("APP_ENV", "development")
        self.log_level = env.get("LOG_LEVEL", "INFO").upper()
        self.api_version = API_VERSION
