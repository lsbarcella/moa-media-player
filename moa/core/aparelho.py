# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""O "Aparelho de CD": o que a tela de colocar um disco mostra e faz. Sem GTK.

É para a cópia de CD o que o `Radio` é para a música: aqui moram os TEXTOS do
visor ("COPIANDO: Faixa 3 de 12") e a máquina de estados; a tela só desenha.
O trabalho pesado fica no `Copiador` (`ripper.py`), numa thread. Desenho
aprovado: opção A de `docs/preview/colocar-disco-opcoes.html` (ADR-0018).

Para o autor (vem de TypeScript): `despachar` é a "ponte" entre a thread da
cópia e a tela. Em produção ele entrega a função à thread principal (`GLib.idle_add`,
como um `postMessage`); nos testes roda na hora.
"""

import logging
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio  # noqa: E402

from moa.core.ripper import DISPOSITIVO_PADRAO, Copiador, Progresso, Resultado  # noqa: E402

log = logging.getLogger(__name__)

MSG_SEM_DISCO = ("Não encontrei o disco. Veja se o CD está com a parte brilhante para baixo "
                 "e feche a gaveta.")
MSG_FALHOU = "Não consegui copiar este CD. Pode tirar o disco, colocar de novo e tentar outra vez."
MSG_SEM_GAVETA = "Não consegui abrir a gaveta. Aperte o botão do próprio leitor, ao lado dela."


class Momento(Enum):
    INICIO = "inicio"           # esperando o idoso pôr o CD
    COPIANDO = "copiando"
    PRONTO = "pronto"
    SEM_DISCO = "sem_disco"
    FALHOU = "falhou"


@dataclass(frozen=True)
class VisorDoAparelho:
    texto: str              # a linha do visor, em letras grandes
    explicacao: str         # a frase calma logo abaixo
    fracao: float | None    # 0.0 a 1.0 quando está copiando; None nos outros momentos


def ejetar_o_cd(dispositivo: str = DISPOSITIVO_PADRAO) -> bool:
    """Pede ao sistema para abrir a gaveta do leitor. False se não conseguiu."""
    try:
        for unidade in Gio.VolumeMonitor.get().get_connected_drives():
            if unidade.get_identifier("unix-device") == dispositivo and unidade.can_eject():
                unidade.eject_with_operation(Gio.MountUnmountFlags.NONE, None, None, None, None)
                return True
    except Exception:
        log.exception("erro ao abrir a gaveta")
        return False
    log.warning("não achei o leitor %s para abrir a gaveta", dispositivo)
    return False


class AparelhoDeCD:
    def __init__(self, pasta_de_musica: Path,
                 despachar: Callable[[Callable[[], None]], None] | None = None,
                 fonte: Callable[[int], str] | None = None,
                 contar_faixas: Callable[[], int] | None = None,
                 ejetar: Callable[[], bool] = ejetar_o_cd):
        self._pasta = Path(pasta_de_musica)
        self._despachar = despachar or (lambda funcao: funcao())
        self._fonte = fonte
        self._contar = contar_faixas
        self._ejetar = ejetar
        self.momento = Momento.INICIO
        self.progresso: Progresso | None = None
        self.nome_do_disco: str | None = None
        self.total_de_faixas = 0
        self.thread: threading.Thread | None = None
        self._copiador: Copiador | None = None
        self._ouvintes: list[Callable[[], None]] = []
        self._ao_copiar: Callable[[], None] | None = None

    # -- quem quer saber quando algo mudou ---------------------------------------------

    def ao_mudar(self, funcao: Callable[[], None]) -> None:
        self._ouvintes.append(funcao)

    def ao_copiar(self, funcao: Callable[[], None]) -> None:
        """Chamada quando um disco novo chega à pasta (a estante precisa reler a pasta)."""
        self._ao_copiar = funcao

    def _avisar(self) -> None:
        for funcao in list(self._ouvintes):
            funcao()

    # -- o que a tela mostra ---------------------------------------------------------------

    @property
    def copiando(self) -> bool:
        return self.momento == Momento.COPIANDO

    def visor(self) -> VisorDoAparelho:
        if self.momento == Momento.COPIANDO:
            p = self.progresso
            texto = (f"COPIANDO: Faixa {p.faixa} de {p.total}" if p
                     else "COPIANDO: lendo o disco…")
            return VisorDoAparelho(
                texto, "Pode deixar a janela aberta e esperar. Não precisa fazer mais nada.",
                self._fracao_total())
        if self.momento == Momento.PRONTO:
            return VisorDoAparelho(
                f"PRONTO: {self.total_de_faixas} músicas",
                f"O disco “{self.nome_do_disco}” já está na sua estante. Pode tirar o CD do leitor.",
                None)
        if self.momento == Momento.SEM_DISCO:
            return VisorDoAparelho("SEM DISCO NO APARELHO", MSG_SEM_DISCO, None)
        if self.momento == Momento.FALHOU:
            return VisorDoAparelho("NÃO CONSEGUI COPIAR", MSG_FALHOU, None)
        return VisorDoAparelho(
            "ABRA A GAVETA E PONHA O CD",
            "Ponha o CD no leitor do notebook, com a parte brilhante para baixo, e feche a "
            "gaveta. Depois aperte “Já coloquei o disco”.", None)

    def _fracao_total(self) -> float:
        """Quanto do disco inteiro já foi copiado (para a barra)."""
        p = self.progresso
        if p is None or p.total <= 0:
            return 0.0
        return ((p.faixa - 1) + p.fracao) / p.total

    # -- ações -----------------------------------------------------------------------------

    def copiar(self) -> None:
        """"Já coloquei o disco": começa a copiar, numa thread."""
        if self.copiando:
            return
        self.momento = Momento.COPIANDO
        self.progresso = None
        self._copiador = Copiador(self._pasta, fonte=self._fonte, contar_faixas=self._contar,
                                  ao_progredir=self._ao_progredir)
        self.thread = threading.Thread(target=self._trabalhar, args=(self._copiador,),
                                       name="copia-de-cd", daemon=True)
        self._avisar()
        self.thread.start()

    def parar(self) -> None:
        """"Parar de copiar" (ou fechar o app): o Copiador apaga o que já tinha copiado."""
        if self._copiador is not None and self.copiando:
            self._copiador.cancelar()

    def recomecar(self) -> None:
        """Volta ao começo (depois de "Pronto" ou de uma falha), sem apagar nada."""
        if self.copiando:
            return
        self.momento = Momento.INICIO
        self.progresso = None
        self._avisar()

    def abrir_a_gaveta(self) -> bool:
        return self._ejetar()

    def encerrar(self) -> None:
        """Ao fechar o app: cancela a cópia e espera um pouco a pasta provisória ser apagada."""
        self.parar()
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=5)

    # -- na thread da cópia -----------------------------------------------------------------

    def _trabalhar(self, copiador: Copiador) -> None:
        try:
            resultado = copiador.copiar()
        except Exception:
            log.exception("a cópia do CD falhou")
            resultado = Resultado.FALHOU
        self._despachar(lambda: self._terminou(copiador, resultado))

    def _ao_progredir(self, progresso: Progresso) -> None:
        self._despachar(lambda: self._progrediu(progresso))

    # -- de volta à thread principal --------------------------------------------------------

    def _progrediu(self, progresso: Progresso) -> None:
        if self.copiando:
            self.progresso = progresso
            self._avisar()

    def _terminou(self, copiador: Copiador, resultado: Resultado) -> None:
        self.nome_do_disco = copiador.nome_do_disco
        if resultado == Resultado.COPIADO:
            self.momento = Momento.PRONTO
            self.total_de_faixas = self.progresso.total if self.progresso else 0
        elif resultado == Resultado.SEM_DISCO:
            self.momento = Momento.SEM_DISCO
        elif resultado == Resultado.CANCELADO:
            self.momento = Momento.INICIO
        else:
            self.momento = Momento.FALHOU
        self.progresso = None if resultado != Resultado.COPIADO else self.progresso
        self._avisar()
        if resultado == Resultado.COPIADO and self._ao_copiar is not None:
            try:
                self._ao_copiar()
            except Exception:
                log.exception("não consegui atualizar a estante depois da cópia")
