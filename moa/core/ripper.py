# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Copia um CD para a biblioteca ("colocar um disco na estante").

Sem GTK. O idoso nunca vê erro técnico (restrição 5): aqui toda falha vai para
o log e vira um resultado simples (`Resultado`) que a tela traduz em uma frase calma.

Como funciona (ADR-0017):
- Lê o CD com o `cdparanoiasrc` do GStreamer, que corrige riscos, e grava FLAC.
- O disco entra offline com nome "Disco N" e faixas "Faixa 1", "Faixa 2"...
  O M6 (MusicBrainz) corrige os nomes e as capas depois, quando houver internet.
- A cópia é feita numa pasta provisória (`.Disco N.copiando`) e só ganha o nome
  final quando todas as faixas terminam. Assim a estante nunca mostra um disco
  pela metade, e cancelar ou falhar não deixa lixo.
- Nunca mexe em discos que já existem na biblioteca.

Para o autor (vem de TypeScript): `fonte` e `contar_faixas` são "funções
injetadas", como callbacks passados ao construtor. Em produção apontam para o CD
de verdade; nos testes apontam para um gerador de áudio, sem precisar de disco.
"""

import logging
import re
import shutil
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

import gi
import mutagen.flac

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

Gst.init(None)

log = logging.getLogger(__name__)

DISPOSITIVO_PADRAO = "/dev/sr0"
_NOME_DO_DISCO = re.compile(r"^Disco (\d+)$")
SEGUNDOS_POR_FAIXA_MAXIMO = 20 * 60      # trava de segurança: nenhuma faixa de CD passa disso


class Resultado(Enum):
    COPIADO = "copiado"
    CANCELADO = "cancelado"
    SEM_DISCO = "sem_disco"     # leitor vazio ou disco ilegível
    FALHOU = "falhou"


@dataclass(frozen=True)
class Progresso:
    """O que a tela mostra enquanto copia ("Copiando a faixa 3 de 12")."""
    faixa: int          # começa em 1
    total: int
    fracao: float       # 0.0 a 1.0 dentro da faixa atual


def fonte_do_cd(dispositivo: str = DISPOSITIVO_PADRAO) -> Callable[[int], str]:
    """Devolve a função que descreve a origem de uma faixa: o `cdparanoiasrc`."""
    def descrever(numero: int) -> str:
        return f'cdparanoiasrc device="{dispositivo}" track={numero}'
    return descrever


def contar_faixas_do_cd(dispositivo: str = DISPOSITIVO_PADRAO) -> int:
    """Quantas faixas de áudio o CD tem. Zero se não houver disco legível.

    O `cdparanoiasrc` publica o sumário do disco (TOC) ao ficar em PAUSED.
    """
    pipeline = Gst.parse_launch(f'cdparanoiasrc device="{dispositivo}" ! fakesink')
    try:
        pipeline.set_state(Gst.State.PAUSED)
        barramento = pipeline.get_bus()
        fim = Gst.MessageType.TOC | Gst.MessageType.ERROR | Gst.MessageType.ASYNC_DONE
        while True:
            mensagem = barramento.timed_pop_filtered(15 * Gst.SECOND, fim)
            if mensagem is None or mensagem.type == Gst.MessageType.ERROR:
                if mensagem is not None:
                    log.warning("CD ilegível: %s", mensagem.parse_error()[0])
                return 0
            if mensagem.type == Gst.MessageType.TOC:
                toc, _atualizado = mensagem.parse_toc()
                return sum(1 for e in toc.get_entries()
                           if e.get_entry_type() == Gst.TocEntryType.TRACK)
            return 0            # ASYNC_DONE sem TOC: não sei contar
    finally:
        pipeline.set_state(Gst.State.NULL)


def proximo_nome_de_disco(pasta_de_musica: Path) -> str:
    """"Disco 1", "Disco 2"... O primeiro número que ainda não existe.

    Olha também as pastas provisórias, para duas cópias não brigarem pelo nome.
    """
    usados = set()
    if pasta_de_musica.is_dir():
        for filho in pasta_de_musica.iterdir():
            nome = filho.name.removeprefix(".").removesuffix(".copiando")
            achado = _NOME_DO_DISCO.match(nome)
            if achado:
                usados.add(int(achado.group(1)))
    numero = 1
    while numero in usados:
        numero += 1
    return f"Disco {numero}"


def _apagar_provisorias_antigas(pasta_de_musica: Path) -> None:
    """Sobras de uma cópia que foi interrompida (energia, app fechado à força).

    Só mexe em pastas escondidas com o nosso nome (`.Disco N.copiando`).
    """
    for filho in pasta_de_musica.iterdir():
        if filho.is_dir() and filho.name.startswith(".Disco ") and filho.name.endswith(".copiando"):
            log.info("apagando sobra de cópia interrompida: %s", filho.name)
            shutil.rmtree(filho, ignore_errors=True)


class Copiador:
    """Copia um CD, faixa por faixa. Use `copiar()` numa thread, nunca na da tela."""

    def __init__(self, pasta_de_musica: Path,
                 fonte: Callable[[int], str] | None = None,
                 contar_faixas: Callable[[], int] | None = None,
                 ao_progredir: Callable[[Progresso], None] | None = None):
        self._pasta = Path(pasta_de_musica)
        self._fonte = fonte or fonte_do_cd()
        self._contar = contar_faixas or contar_faixas_do_cd
        self._ao_progredir = ao_progredir or (lambda _p: None)
        self._cancelar = threading.Event()
        self.nome_do_disco: str | None = None       # preenchido quando a cópia termina

    def cancelar(self) -> None:
        """Pode ser chamado de qualquer thread (o botão "Parar" da tela)."""
        self._cancelar.set()

    def copiar(self) -> Resultado:
        provisoria: Path | None = None
        try:
            total = self._contar()
            if total <= 0:
                return Resultado.SEM_DISCO
            self._pasta.mkdir(parents=True, exist_ok=True)
            _apagar_provisorias_antigas(self._pasta)
            nome = proximo_nome_de_disco(self._pasta)
            provisoria = self._pasta / f".{nome}.copiando"
            provisoria.mkdir()
            for numero in range(1, total + 1):
                if self._cancelar.is_set():
                    return self._desistir(provisoria, Resultado.CANCELADO)
                if not self._copiar_faixa(provisoria, nome, numero, total):
                    resultado = (Resultado.CANCELADO if self._cancelar.is_set()
                                 else Resultado.FALHOU)
                    return self._desistir(provisoria, resultado)
            final = self._pasta / nome
            provisoria.rename(final)
            self.nome_do_disco = nome
            log.info("CD copiado para %s (%d faixas)", final, total)
            return Resultado.COPIADO
        except Exception:
            log.exception("falha ao copiar o CD")
            if provisoria is not None:
                shutil.rmtree(provisoria, ignore_errors=True)
            return Resultado.FALHOU

    # -- detalhes --------------------------------------------------------

    def _desistir(self, provisoria: Path, resultado: Resultado) -> Resultado:
        shutil.rmtree(provisoria, ignore_errors=True)
        return resultado

    def _copiar_faixa(self, pasta: Path, disco: str, numero: int, total: int) -> bool:
        destino = pasta / f"Faixa {numero:02d}.flac"
        pipeline = Gst.parse_launch(
            f'{self._fonte(numero)} ! audioconvert ! flacenc ! filesink location="{destino}"'
        )
        try:
            pipeline.set_state(Gst.State.PLAYING)
            barramento = pipeline.get_bus()
            limite = Gst.SECOND * SEGUNDOS_POR_FAIXA_MAXIMO
            esperado = 0
            while esperado < limite:
                if self._cancelar.is_set():
                    return False
                mensagem = barramento.timed_pop_filtered(
                    Gst.SECOND // 2, Gst.MessageType.EOS | Gst.MessageType.ERROR)
                self._ao_progredir(Progresso(numero, total, self._fracao(pipeline)))
                if mensagem is None:
                    esperado += Gst.SECOND // 2
                    continue
                if mensagem.type == Gst.MessageType.ERROR:
                    log.error("erro lendo a faixa %d: %s", numero, mensagem.parse_error()[0])
                    return False
                break               # EOS: terminou a faixa
            else:
                log.error("a faixa %d passou do tempo limite", numero)
                return False
        finally:
            pipeline.set_state(Gst.State.NULL)
        self._ao_progredir(Progresso(numero, total, 1.0))
        return self._etiquetar(destino, disco, numero, total)

    @staticmethod
    def _fracao(pipeline: Gst.Element) -> float:
        """Quanto da faixa já foi lido; 0.0 se o GStreamer ainda não sabe."""
        ok_pos, posicao = pipeline.query_position(Gst.Format.TIME)
        ok_dur, duracao = pipeline.query_duration(Gst.Format.TIME)
        if ok_pos and ok_dur and duracao > 0:
            return max(0.0, min(1.0, posicao / duracao))
        return 0.0

    @staticmethod
    def _etiquetar(arquivo: Path, disco: str, numero: int, total: int) -> bool:
        """Grava as tags mínimas ("Faixa N" do "Disco N") com o mutagen."""
        try:
            flac = mutagen.flac.FLAC(arquivo)
            flac["title"] = f"Faixa {numero}"
            flac["album"] = disco
            flac["tracknumber"] = str(numero)
            flac["tracktotal"] = str(total)
            flac.save()
            return True
        except Exception:
            log.exception("não consegui etiquetar %s", arquivo.name)
            return False
