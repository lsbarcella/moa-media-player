# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Painel do "+" de cada música: "Em qual disco?" (forma b, ADR-0007).

Mostra as CAPAS dos discos montados, com "Disco novo" (tracejado) como primeira.
É um painel dentro da própria janela, não uma janela nova (nada de modal inesperado).
A confirmação aparece na linha da música, com "Desfazer"; fica até a próxima ação.
"""

import logging
import sqlite3

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core import custom_albums  # noqa: E402
from moa.core.contexto import Contexto  # noqa: E402
from moa.ui.widgets import botao, capa_do_disco, caixa_v, limpar, rotulo  # noqa: E402

log = logging.getLogger(__name__)

MSG_FALHA = "Não consegui colocar a música no disco. Tente de novo."


class PlusPanel:
    def __init__(self, contexto: Contexto):
        self.ctx = contexto
        # O "véu" cobre a tela e escurece o fundo; o painel fica no meio.
        self.raiz = Gtk.Box()
        self.raiz.get_style_context().add_class("moa-veu")
        self.painel = caixa_v(12)
        self.painel.get_style_context().add_class("moa-painel")
        self.painel.set_halign(Gtk.Align.CENTER)
        self.painel.set_valign(Gtk.Align.CENTER)
        self.raiz.pack_start(self.painel, True, True, 0)
        self.primeiro_botao: Gtk.Widget | None = None
        self.atualizar()

    def atualizar(self) -> None:
        ctx = self.ctx
        faixa = ctx.session.faixa_do_painel
        limpar(self.painel)
        self.primeiro_botao = None
        if faixa is None:
            self.raiz.hide()
            self.raiz.set_no_show_all(True)
            return
        self.raiz.set_no_show_all(False)
        self.painel.pack_start(rotulo(f"Colocar “{faixa.title}” em outro disco", "moa-grande"),
                               False, False, 0)
        self.painel.pack_start(rotulo("Em qual disco?", "moa-forte"), False, False, 0)

        grade = Gtk.FlowBox()
        grade.set_selection_mode(Gtk.SelectionMode.NONE)
        grade.set_activate_on_single_click(True)
        grade.set_row_spacing(12)
        grade.set_column_spacing(12)
        grade.set_max_children_per_line(4)
        grade.add(self._peca_disco_novo())
        for montado in ctx.montados:
            grade.add(self._peca_montado(montado))
        self.painel.pack_start(grade, False, False, 0)
        self.painel.pack_start(botao("Cancelar", ao_clicar=ctx.session.fechar_painel_mais),
                               False, False, 0)
        self.raiz.show_all()

    def _peca_disco_novo(self) -> Gtk.Widget:
        peca = caixa_v(8)
        tracejado = Gtk.Box()
        tracejado.get_style_context().add_class("moa-novo")
        tracejado.set_size_request(150, 150)
        tracejado.pack_start(rotulo("＋", "moa-mais-grande", quebrar=False, centro=True), True, True, 0)
        peca.pack_start(tracejado, False, False, 0)
        peca.pack_start(rotulo("Disco novo", "moa-forte", centro=True), False, False, 0)
        b = Gtk.Button()
        b.add(peca)
        b.get_style_context().add_class("moa-disco")
        b.connect("clicked", lambda _b: self._disco_novo())
        self.primeiro_botao = b
        return b

    def _peca_montado(self, montado) -> Gtk.Widget:
        peca = caixa_v(8)
        peca.pack_start(capa_do_disco(self.ctx, montado, 150), False, False, 0)
        peca.pack_start(rotulo(montado.title, "moa-forte", centro=True, largura_maxima=14),
                        False, False, 0)
        b = Gtk.Button()
        b.add(peca)
        b.get_style_context().add_class("moa-disco")
        b.connect("clicked", lambda _b, m=montado: self._colocar_em(m))
        return b

    # -- ações -------------------------------------------------------------------------------------

    def _colocar_em(self, montado) -> None:
        ctx = self.ctx
        faixa = ctx.session.faixa_do_painel
        caminho = str(faixa.path)
        ctx.session.acao()
        ctx.session.fechar_painel_mais()
        try:
            nova = custom_albums.adicionar_faixa(ctx.banco, montado.id, caminho)
        except sqlite3.Error:
            log.exception("não consegui adicionar a faixa ao disco montado")
            ctx.session.mostrar_aviso(MSG_FALHA, ancora=caminho)
            return
        if not nova:
            ctx.session.mostrar_aviso(f"Esta música já está no disco “{montado.title}”.",
                                      ancora=caminho)
            return
        ctx.recarregar()

        def desfazer() -> None:
            custom_albums.remover_faixa(ctx.banco, montado.id, caminho)
            ctx.recarregar()

        ctx.session.mostrar_aviso(f"Está no disco “{montado.title}”.", desfazer, ancora=caminho)

    def _disco_novo(self) -> None:
        ctx = self.ctx
        faixa = ctx.session.faixa_do_painel
        caminho = str(faixa.path)
        ctx.session.acao()
        ctx.session.fechar_painel_mais()
        nome = custom_albums.sugerir_nome([d.title for d in ctx.montados + ctx.caixa])
        try:
            mix_id = custom_albums.criar(ctx.banco, nome, [caminho])
        except sqlite3.Error:
            log.exception("não consegui criar o disco montado")
            ctx.session.mostrar_aviso(MSG_FALHA, ancora=caminho)
            return
        ctx.recarregar()

        def desfazer() -> None:
            custom_albums.apagar(ctx.banco, mix_id)
            ctx.recarregar()

        ctx.session.mostrar_aviso(f"Criei o disco “{nome}” com esta música.", desfazer,
                                  ancora=caminho)
