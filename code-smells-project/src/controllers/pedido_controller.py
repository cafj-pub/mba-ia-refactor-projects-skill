from collections import Counter

from src.config.constants import STATUS_PEDIDO_APROVADO, STATUS_PEDIDO_CANCELADO, STATUS_PEDIDO_VALIDOS
from src.utils.errors import NotFoundError, ValidationError
from src.utils.validators import require_dict, to_positive_int


class PedidoController:
    def __init__(self, pedido_model, produto_model, usuario_model, notification_service):
        self._pedidos = pedido_model
        self._produtos = produto_model
        self._usuarios = usuario_model
        self._notificacoes = notification_service

    def criar(self, dados):
        require_dict(dados)
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            raise ValidationError("Usuario ID é obrigatório")
        if not itens or not isinstance(itens, list):
            raise ValidationError("Pedido deve ter pelo menos 1 item")
        if not self._usuarios.buscar_por_id(usuario_id):
            raise NotFoundError("Usuário não encontrado")

        itens_validados = self._precificar_itens(itens)
        total = sum(item["preco_unitario"] * item["quantidade"] for item in itens_validados)

        pedido_id = self._pedidos.criar(usuario_id, itens_validados, total)
        self._notificacoes.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def _precificar_itens(self, itens):
        normalizados = []
        for item in itens:
            if not isinstance(item, dict):
                raise ValidationError("Item de pedido inválido")
            normalizados.append({
                "produto_id": to_positive_int(item.get("produto_id"), "produto_id inválido"),
                "quantidade": to_positive_int(item.get("quantidade"), "Quantidade inválida"),
            })

        produtos = self._produtos.buscar_por_ids(item["produto_id"] for item in normalizados)
        quantidade_por_produto = Counter()
        for item in normalizados:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado")
            quantidade_por_produto[item["produto_id"]] += item["quantidade"]
            if produto["estoque"] < quantidade_por_produto[item["produto_id"]]:
                raise ValidationError("Estoque insuficiente para " + produto["nome"])
            item["preco_unitario"] = produto["preco"]
            item["nome"] = produto["nome"]
        return normalizados

    def listar_todos(self):
        return self._pedidos.listar()

    def listar_por_usuario(self, usuario_id):
        return self._pedidos.listar_por_usuario(usuario_id)

    def atualizar_status(self, pedido_id, dados):
        dados = dados if isinstance(dados, dict) else {}
        novo_status = dados.get("status", "")
        if novo_status not in STATUS_PEDIDO_VALIDOS:
            raise ValidationError("Status inválido")

        if not self._pedidos.atualizar_status(pedido_id, novo_status):
            raise NotFoundError("Pedido não encontrado")

        if novo_status == STATUS_PEDIDO_APROVADO:
            self._notificacoes.pedido_aprovado(pedido_id)
        elif novo_status == STATUS_PEDIDO_CANCELADO:
            self._notificacoes.pedido_cancelado(pedido_id)
