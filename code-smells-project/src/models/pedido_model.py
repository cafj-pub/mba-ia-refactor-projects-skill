from src.config.constants import STATUS_PEDIDO_PENDENTE
from src.utils.errors import ValidationError

_SELECT_PEDIDOS_COM_ITENS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
           pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def _agrupar_pedidos(rows):
    pedidos = {}
    for row in rows:
        pedido = pedidos.setdefault(row["id"], {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        })
        if row["item_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


class PedidoModel:
    def __init__(self, get_connection):
        self._get_connection = get_connection

    def criar(self, usuario_id, itens, total):
        """Cria pedido, itens e baixa estoque numa única transação.

        `itens` é uma lista de dicts com produto_id, quantidade, preco_unitario e nome.
        """
        conn = self._get_connection()
        with conn:
            pedido_id = conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PEDIDO_PENDENTE, total),
            ).lastrowid
            conn.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                [(pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]) for item in itens],
            )
            for item in itens:
                atualizado = conn.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                ).rowcount
                if not atualizado:
                    # Exceção dentro do bloco `with` provoca rollback de todo o pedido.
                    raise ValidationError("Estoque insuficiente para " + item["nome"])
        return pedido_id

    def listar(self):
        rows = self._get_connection().execute(_SELECT_PEDIDOS_COM_ITENS + " ORDER BY p.id, i.id").fetchall()
        return _agrupar_pedidos(rows)

    def listar_por_usuario(self, usuario_id):
        rows = self._get_connection().execute(
            _SELECT_PEDIDOS_COM_ITENS + " WHERE p.usuario_id = ? ORDER BY p.id, i.id", (usuario_id,)
        ).fetchall()
        return _agrupar_pedidos(rows)

    def atualizar_status(self, pedido_id, status):
        conn = self._get_connection()
        with conn:
            return conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id)).rowcount > 0

    def resumo_vendas(self):
        row = self._get_connection().execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   COALESCE(SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END), 0) AS pendentes,
                   COALESCE(SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END), 0) AS aprovados,
                   COALESCE(SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END), 0) AS cancelados
            FROM pedidos
            """
        ).fetchone()
        return dict(row)

    def contar(self):
        return self._get_connection().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
