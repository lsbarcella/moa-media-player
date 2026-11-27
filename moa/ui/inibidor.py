# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Impede que o notebook durma ou apague a tela enquanto a música toca.

Sem isso, o descanso de tela cortaria a música no meio, e o idoso não saberia
por quê. O `Gtk.Application.inhibit` pede ao sistema para não suspender; ao
pausar ou parar, devolvemos o pedido (o "cookie"), e o notebook volta a poder
descansar. É como pendurar um aviso de "não perturbe" só enquanto toca.
"""

import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

log = logging.getLogger(__name__)

MOTIVO = "Tocando música"
FLAGS = Gtk.ApplicationInhibitFlags.SUSPEND | Gtk.ApplicationInhibitFlags.IDLE


class Inibidor:
    """Liga o pedido quando começa a tocar e o desliga quando para ou pausa."""

    def __init__(self, aplicacao, janela, radio):
        self._app = aplicacao
        self._janela = janela
        self._radio = radio
        self._cookie = 0
        radio.ao_mudar(self.atualizar)

    @property
    def ativo(self) -> bool:
        return self._cookie != 0

    def atualizar(self) -> None:
        if self._radio.tocando and not self.ativo:
            self._ligar()
        elif not self._radio.tocando and self.ativo:
            self.soltar()

    def _ligar(self) -> None:
        try:
            self._cookie = self._app.inhibit(self._janela, FLAGS, MOTIVO)
        except Exception:                 # sem o pedido a música ainda toca; só registra
            log.exception("não consegui impedir a suspensão")
            self._cookie = 0

    def soltar(self) -> None:
        """Devolve o pedido. Chamado ao pausar e também ao fechar a janela."""
        if self._cookie:
            try:
                self._app.uninhibit(self._cookie)
            except Exception:
                log.exception("não consegui liberar a suspensão")
            self._cookie = 0
