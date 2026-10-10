import hmac
import logging

from src.utils.errors import ForbiddenError

logger = logging.getLogger(__name__)

ENDPOINTS_PUBLICOS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


class SistemaController:
    """Fluxos de sistema: boas-vindas, health check e manutenção administrativa."""

    def __init__(self, settings, produto_model, usuario_model, pedido_model, clear_database):
        self._settings = settings
        self._produtos = produto_model
        self._usuarios = usuario_model
        self._pedidos = pedido_model
        self._clear_database = clear_database

    def boas_vindas(self):
        return {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": self._settings.api_version,
            "endpoints": ENDPOINTS_PUBLICOS,
        }

    def health(self):
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self._produtos.contar(),
                "usuarios": self._usuarios.contar(),
                "pedidos": self._pedidos.contar(),
            },
            "versao": self._settings.api_version,
            "ambiente": self._settings.environment,
        }

    def reset_database(self, token_informado):
        token_esperado = self._settings.admin_token
        if not token_esperado or not hmac.compare_digest(token_informado or "", token_esperado):
            raise ForbiddenError("Acesso negado")
        self._clear_database()
        logger.warning("Banco de dados resetado via endpoint administrativo")
