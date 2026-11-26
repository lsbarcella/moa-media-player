# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tela "Minha estante": os discos à vista, um clique para pegar um disco.

Desenho aprovado em `docs/preview/moa-preview.html`. A estante lembra
(decisão do autor): "Continuar a ouvir", "Ouvidos há pouco" e o lugar vazio
"Em uso no rádio" quando o disco está no rádio.
"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.contexto import Contexto  # noqa: E402
from moa.core.session import Tela  # noqa: E402
from moa.ui.widgets import aviso, botao, capa_do_disco, caixa_h, caixa_v, limpar, rotulo  # noqa: E402

TEXTO_CARREGANDO = "Estou procurando os seus discos..."
TEXTO_VAZIO = ("Ainda não há discos aqui. Quando houver músicas na pasta de música, "
               "os discos aparecem na estante.")


class ShelfView:
    def __init__(self, contexto: Contexto):
        self.ctx = contexto
        self.raiz = caixa_v(18)
        self.raiz.set_border_width(24)
        self.raiz.set_halign(Gtk.Align.FILL)
        self.botao_principal: Gtk.Widget | None = None
        self.atualizar()

    # -- desenho ---------------------------------------------------------------------

    def atualizar(self) -> None:
        ctx = self.ctx
        limpar(self.raiz)
        self.botao_principal = None
        if ctx.session.aviso is not None:
            a = ctx.session.aviso
            self.raiz.pack_start(aviso(a.texto, ctx.session.desfazer if a.desfazer else None, a.rotulo_do_desfazer),
                                 False, False, 0)

        if not ctx.discos and not ctx.montados:
            texto = TEXTO_CARREGANDO if ctx.carregando else TEXTO_VAZIO
            cartao = caixa_v(0)
            cartao.get_style_context().add_class("moa-cartao")
            cartao.pack_start(rotulo(texto), False, False, 0)
            self.raiz.pack_start(cartao, False, False, 0)
            self.raiz.show_all()
            return

        self._desenhar_acoes()
        self._desenhar_continuar()
        recentes = [d for d in (ctx.disco(i) for i in ctx.memoria.recentes(ctx.ids_dos_discos)) if d]
        self._desenhar_prateleira("Ouvidos há pouco", recentes)
        self._desenhar_prateleira("Meus discos", ctx.discos)
        self._desenhar_prateleira("Discos que montei", ctx.montados)
        self.raiz.show_all()

    def _desenhar_acoes(self) -> None:
        linha = caixa_h(14)
        criar = botao("Criar uma playlist", "moa-pri", "moa-grande", icone_nome="mais",
                      ao_clicar=self._criar_playlist)
        linha.pack_start(criar, False, False, 0)
        n = len(self.ctx.caixa)
        linha.pack_start(botao(f"A Caixa ({n} {'disco' if n == 1 else 'discos'})", "moa-grande",
                               icone_nome="caixa", ao_clicar=self._abrir_a_caixa), False, False, 0)
        self.botao_principal = criar
        self.raiz.pack_start(linha, False, False, 0)

    def _abrir_a_caixa(self) -> None:
        self.ctx.session.ir_para(Tela.CAIXA)

    def _criar_playlist(self) -> None:
        self.ctx.session.acao()
        self.ctx.novo_rascunho()
        self.ctx.session.ir_para(Tela.PLAYLIST)

    def _desenhar_continuar(self) -> None:
        ctx = self.ctx
        if ctx.radio.tem_disco:
            return
        onde = ctx.memoria.onde_parou(ctx.ids_dos_discos)
        if onde is None:
            return
        disco = ctx.disco(onde.album_id)
        if disco is None or onde.indice >= len(disco.tracks):
            return
        cartao = caixa_h(16)
        cartao.get_style_context().add_class("moa-cartao")
        cartao.get_style_context().add_class("moa-continuar")
        cartao.pack_start(
            rotulo(f"Você parou em {disco.title}, faixa {onde.indice + 1}."), True, True, 0)
        b = botao("Continuar a ouvir", "moa-pri", "moa-grande",
                  ao_clicar=lambda: self._continuar(disco, onde))
        cartao.pack_start(b, False, False, 0)
        self.botao_principal = b
        self.raiz.pack_start(cartao, False, False, 0)

    def _desenhar_prateleira(self, titulo: str, discos) -> None:
        if not discos:
            return
        secao = caixa_v(12)
        placa = Gtk.Box()
        placa.get_style_context().add_class("moa-placa")
        placa.pack_start(rotulo(titulo, quebrar=False), False, False, 0)
        placa.set_halign(Gtk.Align.START)
        secao.pack_start(placa, False, False, 0)

        grade = Gtk.FlowBox()
        grade.set_selection_mode(Gtk.SelectionMode.NONE)
        grade.set_activate_on_single_click(True)       # um clique ativa (CLAUDE.md, seção 9)
        grade.set_homogeneous(True)
        grade.set_min_children_per_line(1)
        grade.set_max_children_per_line(8)
        grade.set_column_spacing(18)
        grade.set_row_spacing(20)
        for disco in discos:
            grade.add(self._peca(disco))
        moldura = caixa_v(0)
        moldura.get_style_context().add_class("moa-tabua")
        moldura.pack_start(grade, False, False, 0)
        secao.pack_start(moldura, False, False, 0)
        self.raiz.pack_start(secao, False, False, 0)
        if self.botao_principal is None:
            self.botao_principal = grade.get_child_at_index(0).get_child()

    def _peca(self, disco) -> Gtk.Widget:
        ctx = self.ctx
        peca = caixa_v(8)
        if ctx.radio.tem_disco and ctx.radio.disco.id == disco.id:
            vazio = Gtk.Box()
            vazio.get_style_context().add_class("moa-vazio")
            vazio.set_size_request(150, 150)
            vazio.pack_start(rotulo("Em uso no rádio", centro=True), True, True, 8)
            peca.pack_start(vazio, False, False, 0)
            peca.pack_start(rotulo("Ir ao rádio", "moa-forte", centro=True), False, False, 0)
            clique = lambda: ctx.session.ir_para(Tela.RADIO)
        else:
            peca.pack_start(capa_do_disco(ctx, disco), False, False, 0)
            peca.pack_start(rotulo(disco.title, "moa-forte", centro=True, largura_maxima=14), False, False, 0)
            clique = lambda d=disco: self._pegar(d)
        b = Gtk.Button()
        b.add(peca)
        b.get_style_context().add_class("moa-disco")
        b.connect("clicked", lambda _b: clique())
        return b

    # -- ações ---------------------------------------------------------------------------

    def _pegar(self, disco) -> None:
        self.ctx.session.acao()
        self.ctx.radio.abrir_disco(disco)
        self.ctx.session.ir_para(Tela.RADIO)

    def _continuar(self, disco, onde) -> None:
        self.ctx.session.acao()
        self.ctx.radio.abrir_disco(disco, indice=onde.indice, posicao=onde.segundos, tocar=True)
        self.ctx.session.ir_para(Tela.RADIO)

    def foco_inicial(self) -> Gtk.Widget | None:
        return self.botao_principal
