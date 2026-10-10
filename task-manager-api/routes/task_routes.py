from flask import Blueprint, jsonify, request


def create_task_blueprint(controller):
    task_bp = Blueprint('tasks', __name__)

    @task_bp.route('/tasks', methods=['GET'])
    def get_tasks():
        return jsonify(controller.list_tasks()), 200

    @task_bp.route('/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        return jsonify(controller.get_task(task_id)), 200

    @task_bp.route('/tasks', methods=['POST'])
    def create_task():
        return jsonify(controller.create_task(request.get_json(silent=True))), 201

    @task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        return jsonify(controller.update_task(task_id, request.get_json(silent=True))), 200

    @task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        controller.delete_task(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200

    @task_bp.route('/tasks/search', methods=['GET'])
    def search_tasks():
        args = request.args
        results = controller.search_tasks(
            args.get('q', ''), args.get('status', ''), args.get('priority', ''), args.get('user_id', '')
        )
        return jsonify(results), 200

    @task_bp.route('/tasks/stats', methods=['GET'])
    def task_stats():
        return jsonify(controller.task_stats()), 200

    return task_bp
