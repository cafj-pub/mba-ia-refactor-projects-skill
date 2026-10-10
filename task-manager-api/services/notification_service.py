import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 10


class NotificationService:
    """Envia notificações por e-mail. Sem SMTP configurado, apenas registra em log."""

    def __init__(self, host='', port=587, user='', password=''):
        self._host = host
        self._port = port
        self._user = user
        self._password = password

    @property
    def enabled(self):
        return bool(self._host and self._user and self._password)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.info('SMTP não configurado; e-mail "%s" não enviado', subject)
            return False

        message = EmailMessage()
        message['From'] = self._user
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)
        try:
            with smtplib.SMTP(self._host, self._port, timeout=SMTP_TIMEOUT_SECONDS) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.send_message(message)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception('Falha ao enviar e-mail "%s"', subject)
            return False

    def notify_task_assigned(self, user, task):
        subject = f'Nova task atribuída: {task.title}'
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f'Prioridade: {task.priority}\nStatus: {task.status}'
        )
        return self.send_email(user.email, subject, body)
