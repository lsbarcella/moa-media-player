# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Onde o idoso parou e os discos ouvidos há pouco (M2). Sem GTK.

Tudo mora no banco SQLite (ADR-0008). As gravações feitas enquanto o app roda
são de MELHOR ESFORÇO: se o banco estiver ocupado (por exemplo, a varredura
gravando), o erro só vai para o log. Perder uma posição de poucos segundos não
vale uma mensagem técnica para o idoso (restrição 5).
"""

import logging
import sqlite3
from dataclasses import dataclass
from typing import Collection

from moa.core.db import Database

log = logging.getLogger(__name__)

# Guardamos 6 discos recentes; a estante mostra até 5 (o sexto cobre o caso de
# um deles ter sumido da coleção).
RECENTES_GUARDADOS = 6
RECENTES_NA_ESTANTE = 5


@dataclass(frozen=True)
class OndeParou:
    """Disco, faixa (a partir de 0) e segundo em que a música parou."""

    album_id: str
    indice: int
    segundos: float


class Memoria:
    """Lê e grava o que o app lembra entre uma abertura e outra."""

    def __init__(self, banco: Database):
        self._banco = banco

    def guardar_onde_parou(self, album_id: str, indice: int, segundos: float) -> None:
        try:
            self._banco.save_playback(album_id, indice, max(0.0, segundos))
        except sqlite3.Error as erro:
            log.warning("não consegui guardar onde parou: %s", erro)

    def onde_parou(self, discos_existentes: Collection[str]) -> OndeParou | None:
        """Onde parou, ou None se nunca tocou ou se o disco não existe mais."""
        try:
            guardado = self._banco.load_playback()
        except sqlite3.Error as erro:
            log.warning("não consegui ler onde parou: %s", erro)
            return None
        if guardado is None or guardado[0] not in discos_existentes:
            return None
        return OndeParou(*guardado)

    def registrar_recente(self, album_id: str) -> None:
        try:
            self._banco.touch_recent(album_id, RECENTES_GUARDADOS)
        except sqlite3.Error as erro:
            log.warning("não consegui guardar o disco recente: %s", erro)

    def recentes(self, discos_existentes: Collection[str],
                 limite: int = RECENTES_NA_ESTANTE) -> list[str]:
        """Ids dos discos ouvidos há pouco (só os que ainda existem), do mais novo."""
        try:
            todos = self._banco.load_recents()
        except sqlite3.Error as erro:
            log.warning("não consegui ler os recentes: %s", erro)
            return []
        return [d for d in todos if d in discos_existentes][:limite]
