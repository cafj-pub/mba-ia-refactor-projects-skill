PRODUTO_CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")
_SELECT_PRODUTO = f"SELECT {', '.join(PRODUTO_CAMPOS)} FROM produtos"


def _row_to_produto(row):
    return {campo: row[campo] for campo in PRODUTO_CAMPOS}


class ProdutoModel:
    def __init__(self, get_connection):
        self._get_connection = get_connection

    def listar(self):
        rows = self._get_connection().execute(_SELECT_PRODUTO).fetchall()
        return [_row_to_produto(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._get_connection().execute(f"{_SELECT_PRODUTO} WHERE id = ?", (produto_id,)).fetchone()
        return _row_to_produto(row) if row else None

    def buscar_por_ids(self, produto_ids):
        ids = list(set(produto_ids))
        if not ids:
            return {}
        placeholders = ", ".join("?" for _ in ids)
        rows = self._get_connection().execute(
            f"{_SELECT_PRODUTO} WHERE id IN ({placeholders})", ids
        ).fetchall()
        return {row["id"]: _row_to_produto(row) for row in rows}

    def pesquisar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        clausulas, params = [], []
        if termo:
            clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            clausulas.append("categoria = ?")
            params.append(categoria)
        if preco_min is not None:
            clausulas.append("preco >= ?")
            params.append(preco_min)
        if preco_max is not None:
            clausulas.append("preco <= ?")
            params.append(preco_max)

        where = f" WHERE {' AND '.join(clausulas)}" if clausulas else ""
        rows = self._get_connection().execute(_SELECT_PRODUTO + where, params).fetchall()
        return [_row_to_produto(row) for row in rows]

    def criar(self, nome, descricao, preco, estoque, categoria):
        conn = self._get_connection()
        with conn:
            cursor = conn.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        conn = self._get_connection()
        with conn:
            conn.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def deletar(self, produto_id):
        conn = self._get_connection()
        with conn:
            conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def contar(self):
        return self._get_connection().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
