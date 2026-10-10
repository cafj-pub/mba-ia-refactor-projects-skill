import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Ponto único para notificações. Hoje apenas registra em log; um provedor real
    (e-mail, SMS, push) pode ser plugado aqui sem alterar os controllers."""

    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Notificação: pedido %s criado para usuário %s (email/sms/push)", pedido_id, usuario_id)

    def pedido_aprovado(self, pedido_id):
        logger.info("Notificação: pedido %s aprovado, preparar envio", pedido_id)

    def pedido_cancelado(self, pedido_id):
        logger.info("Notificação: pedido %s cancelado", pedido_id)
