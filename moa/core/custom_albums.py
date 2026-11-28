# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Discos montados pelo próprio usuário (M4). Sem GTK.

Um disco montado é VIRTUAL (KTD9): guarda só os caminhos das faixas de outros
discos. Nenhum arquivo de música é copiado, movido ou alterado.
"""

import logging
import uuid
from datetime import date
from typing import Iterable, Mapping

from moa.core.db import Database
from moa.core.models import Album, MixDisc, Track
from moa.core.textutil import fold

log = logging.getLogger(__name__)

PREFIXO_DO_ID = "montado:"


def eh_disco_montado(album_id: str) -> bool:
    return album_id.startswith(PREFIXO_DO_ID)


def sugerir_nome(nomes_existentes: Iterable[str], hoje: date | None = None) -> str:
    """"Meu disco de 26/11", "Meu disco de 26/11 (2)"... sem repetir um nome já usado."""
    hoje = hoje or date.today()
    usados = set(nomes_existentes)
    base = f"Meu disco de {hoje:%d/%m}"
    nome, contador = base, 1
    while nome in usados:
        contador += 1
        nome = f"{base} ({contador})"
    return nome


def criar(db: Database, nome: str, caminhos: list[str]) -> str:
    """Cria o disco montado com as faixas na ordem dada (sem repetir) e devolve o id."""
    sem_repetir = list(dict.fromkeys(caminhos))
    mix_id = PREFIXO_DO_ID + uuid.uuid4().hex[:12]
    db.create_mix(mix_id, nome.strip() or "Meu disco", sem_repetir)
    return mix_id


def adicionar_faixa(db: Database, mix_id: str, caminho: str) -> bool:
    """False quando a faixa já estava no disco (nada é duplicado)."""
    return db.add_mix_track(mix_id, caminho)


def remover_faixa(db: Database, mix_id: str, caminho: str) -> None:
    db.remove_mix_track(mix_id, caminho)


def apagar(db: Database, mix_id: str) -> None:
    """Desfaz o disco montado. As músicas dos outros discos continuam onde estão."""
    db.delete_mix(mix_id)


def carregar(db: Database, faixas_por_caminho: Mapping[str, Track]) -> list[MixDisc]:
    """Os discos montados, com as faixas resolvidas.

    Uma faixa cujo arquivo sumiu da coleção é pulada em silêncio (só vai para o log):
    o disco montado continua abrindo com as outras.
    """
    discos = []
    for mix_id, nome, caminhos in db.load_mixes():
        faixas = []
        for caminho in caminhos:
            faixa = faixas_por_caminho.get(caminho)
            if faixa is None:
                log.info("a faixa %s do disco montado %s não está mais na coleção", caminho, nome)
                continue
            faixas.append(faixa)
        discos.append(MixDisc(id=mix_id, title=nome, tracks=tuple(faixas)))
    return discos


class RascunhoDePlaylist:
    """O disco novo que o usuário está montando, antes de guardar. Sem GTK.

    As músicas marcadas ficam guardadas AQUI, fora da lista que aparece na tela:
    filtrar por disco ou por texto não desmarca nada (decisão do preview, I2).
    """

    TODOS = "todos"

    def __init__(self, nomes_existentes: Iterable[str], hoje: date | None = None):
        self.marcadas: list[str] = []          # caminhos, na ordem em que foram marcadas
        self.disco_do_filtro: str = self.TODOS
        self.busca: str = ""
        self.nome: str = sugerir_nome(nomes_existentes, hoje)
        self.renomeando = False

    def alternar(self, caminho: str) -> None:
        if caminho in self.marcadas:
            self.marcadas.remove(caminho)
        else:
            self.marcadas.append(caminho)

    def esta_marcada(self, caminho: str) -> bool:
        return caminho in self.marcadas

    def filtrar(self, discos: Iterable[Album]) -> list[tuple[Album, Track]]:
        """Pares (disco, faixa) que passam no filtro de disco e no texto digitado."""
        consulta = fold(self.busca.strip())
        achados = []
        for disco in discos:
            if self.disco_do_filtro != self.TODOS and disco.id != self.disco_do_filtro:
                continue
            for faixa in disco.tracks:
                if consulta and consulta not in fold(faixa.title) and consulta not in fold(disco.title):
                    continue
                achados.append((disco, faixa))
        return achados
