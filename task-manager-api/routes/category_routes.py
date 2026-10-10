from flask import Blueprint, jsonify, request


def create_category_blueprint(controller):
    category_bp = Blueprint('categories', __name__)

    @category_bp.route('/categories', methods=['GET'])
    def get_categories():
        return jsonify(controller.list_categories()), 200

    @category_bp.route('/categories', methods=['POST'])
    def create_category():
        return jsonify(controller.create_category(request.get_json(silent=True))), 201

    @category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
    def update_category(cat_id):
        return jsonify(controller.update_category(cat_id, request.get_json(silent=True))), 200

    @category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
    def delete_category(cat_id):
        controller.delete_category(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200

    return category_bp
