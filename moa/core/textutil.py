# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Utilitários de texto para comparar e ordenar nomes em português.

Sem GTK e sem dependências externas: só a biblioteca padrão do Python.
"""

import re
import unicodedata

_DIGITOS = re.compile(r"(\d+)")


def fold(texto: str) -> str:
    """Devolve o texto em minúsculas e sem acentos.

    Serve para comparar e ordenar nomes sem que "Álvaro" vá parar depois de "Zé".
    """
    decomposto = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return sem_acento.casefold()


def natural_key(texto: str) -> list:
    """Chave de ordem "natural": "Faixa 2" vem antes de "Faixa 10".

    O texto é cortado em pedaços de letras e de números. Os números são
    comparados como números, e as letras, sem acento e sem diferença entre
    maiúsculas e minúsculas. Em Python se ordena com uma função-chave
    (`sorted(lista, key=natural_key)`), e não com uma função de comparação.
    """
    pedacos = _DIGITOS.split(fold(texto))
    # O corte sempre alterna texto, número, texto, número... começando por
    # texto (que pode ser vazio), então os pedaços comparados são do mesmo tipo.
    return [int(p) if p.isdigit() else p for p in pedacos]
