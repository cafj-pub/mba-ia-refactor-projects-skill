import os
import secrets

from dotenv import load_dotenv


def _env_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


class Settings:
    """Configuração lida de variáveis de ambiente (e de um arquivo .env, se existir)."""

    def __init__(self, env=None):
        if env is None:
            load_dotenv()
            env = os.environ
        # Sem SECRET_KEY definida, gera uma chave aleatória por processo (adequado só para dev).
        self.secret_key = env.get('SECRET_KEY') or secrets.token_hex(32)
        self.database_url = env.get('DATABASE_URL', 'sqlite:///tasks.db')
        self.debug = _env_bool(env.get('FLASK_DEBUG'))
        self.host = env.get('HOST', '127.0.0.1')
        self.port = int(env.get('PORT', '5000'))
        self.cors_origins = env.get('CORS_ORIGINS', '*')
        self.log_level = env.get('LOG_LEVEL', 'INFO').upper()
        self.api_version = '1.0'
        self.token_max_age_seconds = int(env.get('TOKEN_MAX_AGE_SECONDS', '3600'))
        # Senha do admin criado pelo seed.py; vazia = senha aleatória.
        self.seed_admin_password = env.get('SEED_ADMIN_PASSWORD', '')

        # SMTP vazio = notificações por e-mail desabilitadas (apenas log).
        self.smtp_host = env.get('SMTP_HOST', '')
        self.smtp_port = int(env.get('SMTP_PORT', '587'))
        self.smtp_user = env.get('SMTP_USER', '')
        self.smtp_password = env.get('SMTP_PASSWORD', '')
