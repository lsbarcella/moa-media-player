# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Varredura da pasta de música em segundo plano (KTD6).

A janela aparece na hora, com o que já estava no cache; a varredura roda numa
thread e, quando termina, entrega o resultado à thread principal com
`GLib.idle_add` (como um `postMessage` de Web Worker para a página).

Regra do SQLite: uma conexão por thread. A thread abre o PRÓPRIO `Database`
pelo caminho do arquivo e nunca usa a conexão da janela.
"""

import logging
import threading
from pathlib import Path

from gi.repository import GLib

from moa.core.contexto import Contexto
from moa.core.covers import refresh_covers
from moa.core.db import Database
from moa.core.library import refresh_library

log = logging.getLogger(__name__)


def varrer(caminho_do_banco: Path, pasta_musica: Path, pasta_miniaturas: Path):
    """O trabalho em si (sem GTK): devolve (discos, miniaturas). Roda em qualquer thread."""
    banco = Database(caminho_do_banco)
    try:
        discos = refresh_library(pasta_musica, banco)
        miniaturas = refresh_covers(discos, banco, pasta_miniaturas)
        return discos, miniaturas
    finally:
        banco.close()


class Carregador:
    def __init__(self, contexto: Contexto, caminho_do_banco: Path, pasta_miniaturas: Path):
        self._contexto = contexto
        self._caminho_do_banco = caminho_do_banco
        self._pasta_miniaturas = pasta_miniaturas
        self.thread: threading.Thread | None = None

    def iniciar(self) -> None:
        self.thread = threading.Thread(target=self._trabalhar, name="varredura", daemon=True)
        self.thread.start()

    def _trabalhar(self) -> None:
        try:
            discos, miniaturas = varrer(self._caminho_do_banco, self._contexto.pasta_musica,
                                        self._pasta_miniaturas)
        except Exception:                      # nunca derruba o app nem assusta o idoso
            log.exception("a varredura da pasta de música falhou")
            discos, miniaturas = list(self._contexto.discos), dict(self._contexto.miniaturas)
        GLib.idle_add(self._entregar, discos, miniaturas)

    def _entregar(self, discos, miniaturas) -> bool:
        self._contexto.definir_colecao(discos, miniaturas)
        return False                           # False: não repetir este idle
