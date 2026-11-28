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
from moa.core import box, musicbrainz
from moa.core.covers import refresh_covers
from moa.core.db import Database
from moa.core.library import refresh_library

log = logging.getLogger(__name__)


def varrer(caminho_do_banco: Path, pasta_musica: Path, pasta_miniaturas: Path):
    """O trabalho em si (sem GTK): devolve (discos, miniaturas). Roda em qualquer thread."""
    banco = Database(caminho_do_banco)
    try:
        discos = refresh_library(pasta_musica, banco)
        miniaturas = refresh_covers(discos, banco, pasta_miniaturas,
                                    escolhas=box.escolhas_de_capa(banco),
                                    alternativas=musicbrainz.capas_baixadas(banco.load_mb()))
        return discos, miniaturas
    finally:
        banco.close()


class Carregador:
    def __init__(self, contexto: Contexto, caminho_do_banco: Path, pasta_miniaturas: Path,
                 atualizador: "musicbrainz.Atualizador | None" = None):
        self._atualizador = atualizador     # rede opcional (M6); None = nunca usa a rede
        self._contexto = contexto
        self._caminho_do_banco = caminho_do_banco
        self._pasta_miniaturas = pasta_miniaturas
        self.thread: threading.Thread | None = None

    def iniciar(self) -> None:
        self.thread = threading.Thread(target=self._trabalhar, name="varredura", daemon=True)
        self.thread.start()

    def reler(self) -> None:
        """Procura a pasta de novo (um CD acabou de ser copiado). Sem rede: só a estante."""
        threading.Thread(target=self._reler, name="releitura", daemon=True).start()

    def _reler(self) -> None:
        try:
            discos, miniaturas = varrer(self._caminho_do_banco, self._contexto.pasta_musica,
                                        self._pasta_miniaturas)
        except Exception:
            log.exception("não consegui reler a pasta depois de copiar o CD")
            return
        GLib.idle_add(self._entregar, discos, miniaturas)

    def _trabalhar(self) -> None:
        try:
            discos, miniaturas = varrer(self._caminho_do_banco, self._contexto.pasta_musica,
                                        self._pasta_miniaturas)
        except Exception:                      # nunca derruba o app nem assusta o idoso
            log.exception("a varredura da pasta de música falhou")
            discos, miniaturas = list(self._contexto._brutos), dict(self._contexto.miniaturas)
        GLib.idle_add(self._entregar, discos, miniaturas)
        self._atualizar_pela_rede(discos, miniaturas)

    def _atualizar_pela_rede(self, discos, miniaturas) -> None:
        """Depois que a estante já apareceu, tenta melhorar nomes e capas. Falha em silêncio.

        O resultado só vale na PRÓXIMA abertura (ADR-0003): fica gravado no banco.
        """
        if self._atualizador is None:
            return
        try:
            self._atualizador.executar(discos, miniaturas)
        except Exception:
            log.exception("a atualização pelo MusicBrainz falhou")

    def _entregar(self, discos, miniaturas) -> bool:
        self._contexto.definir_colecao(discos, miniaturas)
        log.info("estante pronta: %d discos", len(discos))      # tools/measure.py mede até aqui
        return False                           # False: não repetir este idle
