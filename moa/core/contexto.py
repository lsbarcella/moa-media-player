# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tudo o que as telas precisam, num lugar só. Sem GTK.

É como um "objeto de contexto" de um app em TypeScript: a janela cria um
`Contexto` e entrega às telas, que só desenham e chamam as ações dele.
"""

from pathlib import Path
from typing import Callable

from moa.core.config import Preferencias
from moa.core.db import Database
from moa.core.models import Album
from moa.core.player import Player
from moa.core.radio import Radio
from moa.core.session import Session
from moa.core.state import Memoria


class Contexto:
    def __init__(self, banco: Database, preferencias: Preferencias, pasta_musica: Path,
                 sink_factory=None):
        self.banco = banco
        self.preferencias = preferencias
        self.pasta_musica = Path(pasta_musica)
        self.session = Session()
        self.memoria = Memoria(banco)
        self.player = Player(sink_factory=sink_factory)
        self.radio = Radio(self.player, self.memoria, preferencias)
        self.discos: list[Album] = []
        self.miniaturas: dict[str, Path | None] = {}
        self.carregando = True              # a primeira varredura ainda não terminou
        self._ouvintes_da_colecao: list[Callable[[], None]] = []

    def ao_mudar_a_colecao(self, funcao: Callable[[], None]) -> None:
        self._ouvintes_da_colecao.append(funcao)

    def definir_colecao(self, discos: list[Album], miniaturas: dict[str, Path | None]) -> None:
        """Chamado quando a varredura termina (sempre na thread principal)."""
        self.discos = sorted(discos, key=lambda d: d.sort_key)
        self.miniaturas = miniaturas
        self.carregando = False
        for funcao in list(self._ouvintes_da_colecao):
            funcao()

    def disco(self, album_id: str | None) -> Album | None:
        return next((d for d in self.discos if d.id == album_id), None)

    @property
    def ids_dos_discos(self) -> set[str]:
        return {d.id for d in self.discos}

    def encerrar(self) -> None:
        """Ao fechar pelo X: guarda onde parou, solta o som e fecha o banco."""
        self.radio.guardar_posicao()
        self.player.encerrar()
