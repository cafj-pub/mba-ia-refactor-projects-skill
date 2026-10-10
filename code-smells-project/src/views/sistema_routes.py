from flask import Blueprint, jsonify, request


def create_sistema_blueprint(sistema_controller, relatorio_controller):
    bp = Blueprint("sistema", __name__)

    @bp.get("/")
    def index():
        return jsonify(sistema_controller.boas_vindas())

    @bp.get("/health")
    def health_check():
        return jsonify(sistema_controller.health()), 200

    @bp.get("/relatorios/vendas")
    def relatorio_vendas():
        return jsonify({"dados": relatorio_controller.vendas(), "sucesso": True}), 200

    @bp.post("/admin/reset-db")
    def reset_database():
        sistema_controller.reset_database(request.headers.get("X-Admin-Token"))
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    return bp
