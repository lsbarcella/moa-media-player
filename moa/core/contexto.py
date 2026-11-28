# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tudo o que as telas precisam, num lugar só. Sem GTK.

É como um "objeto de contexto" de um app em TypeScript: a janela cria um
`Contexto` e entrega às telas, que só desenham e chamam as ações dele.
"""

import time
from dataclasses import replace
from pathlib import Path
from typing import Callable

from gi.repository import GLib

from moa.core import box, custom_albums, musicbrainz
from moa.core.aparelho import AparelhoDeCD
from moa.core.atualizacao_de_teste import AtualizacaoDeTeste     # ATUALIZACAO_DE_TESTE
from moa.core.custom_albums import RascunhoDePlaylist
from moa.core.config import Preferencias
from moa.core.covers import refresh_covers
from moa.core.db import Database
from moa.core.models import Album, MixDisc
from moa.core.player import Player
from moa.core.radio import Radio
from moa.core.session import Session
from moa.core.state import Memoria


def _na_thread_principal(funcao: Callable[[], None]) -> None:
    def uma_vez() -> bool:
        funcao()
        return False            # False = não repetir
    GLib.idle_add(uma_vez)


class Contexto:
    def __init__(self, banco: Database, preferencias: Preferencias, pasta_musica: Path,
                 sink_factory=None, pasta_miniaturas: Path | None = None):
        self.banco = banco
        self.preferencias = preferencias
        self.pasta_musica = Path(pasta_musica)
        self.session = Session()
        self.memoria = Memoria(banco)
        self.player = Player(sink_factory=sink_factory)
        self.radio = Radio(self.player, self.memoria, preferencias)
        self.pasta_miniaturas = pasta_miniaturas
        # A cópia de CD roda numa thread; `idle_add` leva os avisos dela à thread principal.
        self.aparelho = AparelhoDeCD(self.pasta_musica, despachar=_na_thread_principal)
        self.atualizacao = AtualizacaoDeTeste(despachar=_na_thread_principal)     # ATUALIZACAO_DE_TESTE
        # O que o MusicBrainz trouxe numa abertura ANTERIOR. É lido uma vez, aqui, e não muda até
        # o app abrir de novo: a estante não se altera enquanto o idoso olha para ela (ADR-0003).
        self._camada_mb = banco.load_mb()
        self._brutos: list[Album] = []              # o que a varredura achou, sem as camadas
        self.discos: list[Album] = []               # na estante (sem a Caixa, com nomes editados)
        self.montados: list[MixDisc] = []           # discos montados que estão na estante
        self.caixa: list = []                       # discos e discos montados na Caixa
        self.faixas_por_caminho: dict = {}
        self.rascunho: RascunhoDePlaylist | None = None   # a playlist que está sendo montada
        self.miniaturas: dict[str, Path | None] = {}
        self.carregando = True              # a primeira varredura ainda não terminou
        self.inicio_da_leitura = time.monotonic()
        self.progresso_da_leitura: tuple[str, int, int | None] | None = None   # (etapa, feitos, total)
        self._ouvintes_do_progresso: list[Callable[[], None]] = []
        self._ouvintes_da_colecao: list[Callable[[], None]] = []

    def ao_progredir_a_leitura(self, funcao: Callable[[], None]) -> None:
        self._ouvintes_do_progresso.append(funcao)

    def informar_progresso(self, etapa: str, feitos: int, total: int | None) -> None:
        """Chamado na thread principal enquanto a pasta é lida ("musicas" ou "capas")."""
        self.progresso_da_leitura = (etapa, feitos, total)
        for funcao in list(self._ouvintes_do_progresso):
            funcao()

    def segundos_de_leitura(self) -> float:
        return time.monotonic() - self.inicio_da_leitura

    def ao_mudar_a_colecao(self, funcao: Callable[[], None]) -> None:
        self._ouvintes_da_colecao.append(funcao)

    def definir_colecao(self, albuns: list[Album], miniaturas: dict[str, Path | None]) -> None:
        """Chamado quando a varredura termina (sempre na thread principal)."""
        self._brutos = list(albuns)
        self.miniaturas = miniaturas
        self.carregando = False
        self._recalcular()

    def recarregar(self, capas: bool = False) -> None:
        """Refaz a estante depois de uma ação do usuário (tirar, editar, montar disco).

        Com `capas=True` também refaz as miniaturas (uma capa foi trocada). Roda na
        thread principal: são poucos discos, e o resultado tem que aparecer na hora.
        """
        if capas and self.pasta_miniaturas is not None:
            self.miniaturas = refresh_covers(self._brutos, self.banco, self.pasta_miniaturas,
                                             escolhas=box.escolhas_de_capa(self.banco),
                                             alternativas=musicbrainz.capas_baixadas(self._camada_mb))
        self._recalcular()

    def _recalcular(self) -> None:
        base = musicbrainz.aplicar(self._brutos, self._camada_mb)     # MusicBrainz por cima das tags
        self.faixas_por_caminho = {str(t.path): t for d in base for t in d.tracks}
        montados = custom_albums.carregar(self.banco, self.faixas_por_caminho)
        camadas = box.aplicar_camadas(base, montados, self.banco)         # a escolha do usuário vence
        self.discos = sorted(camadas.estante, key=lambda d: d.sort_key)
        self.montados = sorted(camadas.montados, key=lambda d: d.sort_key)
        self.caixa = sorted(camadas.caixa, key=lambda d: d.sort_key)
        for funcao in list(self._ouvintes_da_colecao):
            funcao()

    def esquecer_arquivos_apagados(self) -> None:
        """Depois de "Apagar de vez": tira da coleção as faixas cujo arquivo não existe mais."""
        restantes = []
        for disco in self._brutos:
            faixas = tuple(t for t in disco.tracks if t.path.exists())
            if faixas:
                restantes.append(replace(disco, tracks=faixas))
        self._brutos = restantes
        self._recalcular()

    def novo_rascunho(self) -> RascunhoDePlaylist:
        nomes = [d.title for d in self.montados + self.caixa]
        self.rascunho = RascunhoDePlaylist(nomes)
        return self.rascunho

    def disco(self, album_id: str | None):
        """Acha um disco (da estante, montado ou da Caixa) pelo id."""
        return next((d for d in self.discos + self.montados + self.caixa if d.id == album_id), None)

    def disco_de_origem(self, faixa) -> Album | None:
        """O disco de verdade a que a faixa pertence (para "do disco X" nos discos montados)."""
        pasta = faixa.path.parent
        return next((a for a in self._brutos if a.folder == pasta), None)

    @property
    def ids_dos_discos(self) -> set[str]:
        return {d.id for d in self.discos + self.montados}

    def encerrar(self) -> None:
        """Ao fechar pelo X: guarda onde parou, solta o som e fecha o banco."""
        self.aparelho.encerrar()
        self.radio.guardar_posicao()
        self.player.encerrar()
