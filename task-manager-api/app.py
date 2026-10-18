import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.auth import Auth
from middlewares.error_handler import register_error_handlers
from models.user import User
from routes.category_routes import create_category_blueprint
from routes.report_routes import create_report_blueprint
from routes.system_routes import create_system_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint
from services.notification_service import NotificationService
from services.token_service import TokenService


def create_app(settings=None):
    """Composition root: config, banco, dependências, blueprints e error handlers."""
    settings = settings or Settings()
    logging.basicConfig(level=settings.log_level, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=settings.secret_key,
    )
    CORS(app, origins=settings.cors_origins)
    db.init_app(app)

    notification_service = NotificationService(
        settings.smtp_host, settings.smtp_port, settings.smtp_user, settings.smtp_password
    )
    token_service = TokenService(settings.secret_key, settings.token_max_age_seconds)
    auth = Auth(token_service, load_user=lambda user_id: db.session.get(User, user_id))

    app.register_blueprint(create_system_blueprint(settings.api_version))
    app.register_blueprint(create_task_blueprint(TaskController(notification_service)))
    app.register_blueprint(create_user_blueprint(UserController(token_service), auth))
    app.register_blueprint(create_report_blueprint(ReportController()))
    app.register_blueprint(create_category_blueprint(CategoryController()))
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


settings = Settings()
app = create_app(settings)

if __name__ == '__main__':
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
