USUARIO_CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
_SELECT_USUARIO = f"SELECT {', '.join(USUARIO_CAMPOS_PUBLICOS)} FROM usuarios"


def _row_to_usuario(row):
    # Nunca inclui o hash da senha.
    return {campo: row[campo] for campo in USUARIO_CAMPOS_PUBLICOS}


class UsuarioModel:
    def __init__(self, get_connection):
        self._get_connection = get_connection

    def listar(self):
        rows = self._get_connection().execute(_SELECT_USUARIO).fetchall()
        return [_row_to_usuario(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._get_connection().execute(f"{_SELECT_USUARIO} WHERE id = ?", (usuario_id,)).fetchone()
        return _row_to_usuario(row) if row else None

    def buscar_credenciais(self, email):
        """Retorna (usuario_publico, senha_hash) para autenticação, ou (None, None)."""
        row = self._get_connection().execute(
            f"SELECT {', '.join(USUARIO_CAMPOS_PUBLICOS)}, senha FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        if row is None:
            return None, None
        return _row_to_usuario(row), row["senha"]

    def criar(self, nome, email, senha_hash, tipo):
        conn = self._get_connection()
        with conn:
            cursor = conn.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
        return cursor.lastrowid

    def contar(self):
        return self._get_connection().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
