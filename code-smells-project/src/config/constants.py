"""Constantes de domínio da loja."""

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"

NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

TIPO_USUARIO_PADRAO = "cliente"

STATUS_PEDIDO_PENDENTE = "pendente"
STATUS_PEDIDO_APROVADO = "aprovado"
STATUS_PEDIDO_CANCELADO = "cancelado"
STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

# Faixas de desconto do relatório de vendas: (faturamento mínimo exclusivo, taxa).
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
