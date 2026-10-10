from flask import Blueprint

from utils.time import utcnow


def create_system_blueprint(api_version):
    system_bp = Blueprint('system', __name__)

    @system_bp.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(utcnow())}

    @system_bp.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': api_version}

    return system_bp
