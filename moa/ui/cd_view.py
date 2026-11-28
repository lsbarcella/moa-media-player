# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tela "Aparelho de CD": colocar um disco novo na estante (ADR-0018).

Opção A do preview `docs/preview/colocar-disco-opcoes.html`: um aparelho antigo,
da mesma família do rádio, com visor que diz o estado em texto. Os textos e os
estados moram em `core/aparelho.py`; aqui só se desenha.

Durante a cópia a tela é redesenhada a cada meio segundo. Para não roubar o foco
do teclado nem piscar, quando só o progresso mudou o desenho é mantido e só o
texto do visor e a barra são atualizados.
"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.aparelho import MSG_SEM_GAVETA, Momento  # noqa: E402
from moa.core.contexto import Contexto  # noqa: E402
from moa.core.session import Tela  # noqa: E402
from moa.ui.widgets import aviso, botao, caixa_h, caixa_v, icone, limpar, rotulo  # noqa: E402


class CDView:
    def __init__(self, contexto: Contexto):
        self.ctx = contexto
        self.raiz = caixa_v(14)
        self.raiz.set_border_width(24)
        self.principal: Gtk.Widget | None = None
        self._desenhado: tuple | None = None        # (momento, aviso) do desenho atual
        self._rotulo_do_visor: Gtk.Label | None = None
        self._barra: Gtk.ProgressBar | None = None
        self._foco_pendente = False
        self.atualizar()

    def ao_entrar(self) -> None:
        self._desenhado = None              # entrou de novo: redesenha e leva o foco ao botão

    def foco_inicial(self) -> Gtk.Widget | None:
        if not self._foco_pendente:
            return None                     # só o progresso mudou: não mexe no foco
        self._foco_pendente = False
        return self.principal

    # -- desenho ---------------------------------------------------------------------------

    def atualizar(self) -> None:
        aparelho = self.ctx.aparelho
        a = self.ctx.session.aviso
        chave = (aparelho.momento, a)
        visor = aparelho.visor()
        if chave == self._desenhado and self._rotulo_do_visor is not None:
            self._rotulo_do_visor.set_text(visor.texto)          # só o progresso andou
            if self._barra is not None and visor.fracao is not None:
                self._barra.set_fraction(visor.fracao)
            return
        self._desenhado = chave
        self._foco_pendente = True
        limpar(self.raiz)
        if a is not None:
            self.raiz.pack_start(aviso(a.texto, self.ctx.session.desfazer if a.desfazer else None,
                                       a.rotulo_do_desfazer), False, False, 0)
        self.raiz.pack_start(self._aparelho(aparelho.momento, visor), False, False, 0)
        self.raiz.show_all()

    def _aparelho(self, momento: Momento, visor) -> Gtk.Widget:
        corpo = caixa_v(14)
        corpo.get_style_context().add_class("moa-radio")      # mesma família do rádio

        moldura = caixa_h(14)
        moldura.get_style_context().add_class("moa-visor")
        moldura.pack_start(icone("disco", lado=72), False, False, 0)
        self._rotulo_do_visor = rotulo(visor.texto, "moa-grande", "moa-forte")
        moldura.pack_start(self._rotulo_do_visor, True, True, 0)
        corpo.pack_start(moldura, False, False, 0)

        self._barra = None
        if visor.fracao is not None:
            self._barra = Gtk.ProgressBar()
            self._barra.get_style_context().add_class("moa-barra")
            self._barra.set_fraction(visor.fracao)
            corpo.pack_start(self._barra, False, False, 0)

        corpo.pack_start(rotulo(visor.explicacao), False, False, 0)
        corpo.pack_start(self._botoes(momento), False, False, 0)
        return corpo

    def _botoes(self, momento: Momento) -> Gtk.Widget:
        linha = caixa_h(14)
        gaveta = botao("Abrir a gaveta", "moa-grande", ao_clicar=self._abrir_a_gaveta)
        if momento == Momento.COPIANDO:
            parar = botao("Parar de copiar", "moa-grande", "moa-perigo", ao_clicar=self._parar)
            linha.pack_start(parar, False, False, 0)
            self.principal = parar
        elif momento == Momento.PRONTO:
            ver = botao("Ver o disco na estante", "moa-pri", "moa-grande", ao_clicar=self._ver_na_estante)
            linha.pack_start(ver, False, False, 0)
            linha.pack_start(gaveta, False, False, 0)
            self.principal = ver
        else:                               # começo, sem disco, falhou
            texto = "Já coloquei o disco" if momento == Momento.INICIO else "Tentar de novo"
            copiar = botao(texto, "moa-pri", "moa-grande", ao_clicar=self._copiar)
            linha.pack_start(gaveta, False, False, 0)
            linha.pack_start(copiar, False, False, 0)
            self.principal = copiar
        return linha

    # -- ações -------------------------------------------------------------------------------

    def _copiar(self) -> None:
        self.ctx.session.acao()
        self.ctx.aparelho.copiar()

    def _parar(self) -> None:
        self.ctx.session.acao()
        self.ctx.aparelho.parar()

    def _abrir_a_gaveta(self) -> None:
        self.ctx.session.acao()
        if not self.ctx.aparelho.abrir_a_gaveta():
            self.ctx.session.mostrar_aviso(MSG_SEM_GAVETA)

    def _ver_na_estante(self) -> None:
        self.ctx.aparelho.recomecar()
        self.ctx.session.ir_para(Tela.ESTANTE)
