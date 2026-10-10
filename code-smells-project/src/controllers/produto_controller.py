import logging

from src.config.constants import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from src.utils.errors import NotFoundError, ValidationError
from src.utils.validators import optional_float, require_dict, require_fields, to_number

logger = logging.getLogger(__name__)

_CAMPOS_OBRIGATORIOS = [
    ("nome", "Nome é obrigatório"),
    ("preco", "Preço é obrigatório"),
    ("estoque", "Estoque é obrigatório"),
]


def _validar_produto(dados):
    require_dict(dados)
    require_fields(dados, _CAMPOS_OBRIGATORIOS)

    nome = dados["nome"]
    preco = to_number(dados["preco"], "Preço inválido")
    estoque = to_number(dados["estoque"], "Estoque inválido")
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if not isinstance(nome, str) or len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {
        "nome": nome,
        "descricao": dados.get("descricao", ""),
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


class ProdutoController:
    def __init__(self, produto_model):
        self._produtos = produto_model

    def listar(self):
        return self._produtos.listar()

    def buscar(self, produto_id):
        produto = self._produtos.buscar_por_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado")
        return produto

    def pesquisar(self, termo, categoria, preco_min, preco_max):
        return self._produtos.pesquisar(
            termo=termo,
            categoria=categoria,
            preco_min=optional_float(preco_min, "preco_min inválido"),
            preco_max=optional_float(preco_max, "preco_max inválido"),
        )

    def criar(self, dados):
        produto = _validar_produto(dados)
        produto_id = self._produtos.criar(**produto)
        logger.info("Produto criado com ID %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, dados):
        self.buscar(produto_id)
        produto = _validar_produto(dados)
        self._produtos.atualizar(produto_id, **produto)

    def deletar(self, produto_id):
        self.buscar(produto_id)
        self._produtos.deletar(produto_id)
        logger.info("Produto %s deletado", produto_id)
