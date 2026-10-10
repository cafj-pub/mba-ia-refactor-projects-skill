import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.sistema_controller import SistemaController
from src.controllers.usuario_controller import UsuarioController
from src.database import connection
from src.database.schema import clear_all
from src.middlewares.error_handler import register_error_handlers
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.notification_service import NotificationService
from src.views.pedido_routes import create_pedido_blueprint
from src.views.produto_routes import create_produto_blueprint
from src.views.sistema_routes import create_sistema_blueprint
from src.views.usuario_routes import create_usuario_blueprint


def create_app(settings=None):
    """Composition root: monta config, banco, dependências, rotas e error handlers."""
    settings = settings or Settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.update(SECRET_KEY=settings.secret_key, DATABASE_PATH=settings.database_path)
    CORS(app, origins=settings.cors_origins)
    connection.init_app(app, settings.seed_admin_password)

    produto_model = ProdutoModel(connection.get_db)
    usuario_model = UsuarioModel(connection.get_db)
    pedido_model = PedidoModel(connection.get_db)

    produto_controller = ProdutoController(produto_model)
    usuario_controller = UsuarioController(usuario_model)
    pedido_controller = PedidoController(pedido_model, produto_model, usuario_model, NotificationService())
    relatorio_controller = RelatorioController(pedido_model)
    sistema_controller = SistemaController(
        settings, produto_model, usuario_model, pedido_model,
        clear_database=lambda: clear_all(connection.get_db()),
    )

    app.register_blueprint(create_sistema_blueprint(sistema_controller, relatorio_controller))
    app.register_blueprint(create_produto_blueprint(produto_controller))
    app.register_blueprint(create_usuario_blueprint(usuario_controller))
    app.register_blueprint(create_pedido_blueprint(pedido_controller))
    register_error_handlers(app)

    return app
