from flask import Blueprint, g, jsonify, request


def create_user_blueprint(controller, auth):
    user_bp = Blueprint('users', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        return jsonify(controller.list_users()), 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        return jsonify(controller.get_user(user_id)), 200

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        # Cadastro com perfil padrão é público; perfis privilegiados exigem admin (regra no controller).
        actor = auth.optional_user()
        return jsonify(controller.create_user(request.get_json(silent=True), actor=actor)), 201

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    @auth.require_auth
    def update_user(user_id):
        return jsonify(controller.update_user(user_id, request.get_json(silent=True), actor=g.current_user)), 200

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    @auth.require_admin
    def delete_user(user_id):
        controller.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    @user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    def get_user_tasks(user_id):
        return jsonify(controller.get_user_tasks(user_id)), 200

    @user_bp.route('/login', methods=['POST'])
    def login():
        return jsonify(controller.login(request.get_json(silent=True))), 200

    return user_bp
