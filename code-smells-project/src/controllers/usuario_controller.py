import logging

from werkzeug.security import check_password_hash, generate_password_hash

from src.config.constants import TIPO_USUARIO_PADRAO
from src.utils.errors import NotFoundError, UnauthorizedError, ValidationError
from src.utils.validators import require_dict

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuario_model):
        self._usuarios = usuario_model

    def listar(self):
        return self._usuarios.listar()

    def buscar(self, usuario_id):
        usuario = self._usuarios.buscar_por_id(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados):
        require_dict(dados)
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")

        usuario_id = self._usuarios.criar(nome, email, generate_password_hash(senha), TIPO_USUARIO_PADRAO)
        logger.info("Usuário criado com ID %s", usuario_id)
        return usuario_id

    def login(self, dados):
        dados = dados if isinstance(dados, dict) else {}
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")

        usuario, senha_hash = self._usuarios.buscar_credenciais(email)
        if not usuario or not check_password_hash(senha_hash, senha):
            logger.info("Falha de login")
            raise UnauthorizedError("Email ou senha inválidos")

        return {campo: usuario[campo] for campo in ("id", "nome", "email", "tipo")}
