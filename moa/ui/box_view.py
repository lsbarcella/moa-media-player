# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Tela "A Caixa": onde ficam os discos que o usuário tirou da estante.

"Apagar de vez" SÓ existe aqui (ADR-0007), com texto claro e dois botões grandes,
com "Manter o disco" em destaque. Tirar da estante nunca apaga arquivos.
"""

import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core import box  # noqa: E402
from moa.core.contexto import Contexto  # noqa: E402
from moa.core.custom_albums import eh_disco_montado  # noqa: E402
from moa.ui.widgets import aviso, botao, capa_do_disco, caixa_h, caixa_v, limpar, rotulo  # noqa: E402

log = logging.getLogger(__name__)

MSG_FALHA_AO_APAGAR = "Não consegui apagar tudo. O que sobrou continua na Caixa."


class BoxView:
    def __init__(self, contexto: Contexto):
        self.ctx = contexto
        self.raiz = caixa_v(14)
        self.raiz.set_border_width(24)
        self.confirmando: str | None = None        # id do disco que está sendo perguntado
        self.primeiro_botao: Gtk.Widget | None = None
        self.atualizar()

    def ao_entrar(self) -> None:
        self.confirmando = None

    def foco_inicial(self) -> Gtk.Widget | None:
        return self.primeiro_botao

    def atualizar(self) -> None:
        ctx = self.ctx
        limpar(self.raiz)
        self.primeiro_botao = None
        a = ctx.session.aviso
        if a is not None:
            self.raiz.pack_start(aviso(a.texto, ctx.session.desfazer if a.desfazer else None,
                                       a.rotulo_do_desfazer), False, False, 0)
        self.raiz.pack_start(
            rotulo("Aqui ficam os discos que você tirou da estante. "
                   "As músicas continuam guardadas no computador.", "moa-forte"), False, False, 0)
        if not ctx.caixa:
            cartao = caixa_v(0)
            cartao.get_style_context().add_class("moa-cartao")
            cartao.pack_start(rotulo("A Caixa está vazia."), False, False, 0)
            self.raiz.pack_start(cartao, False, False, 0)
        for disco in ctx.caixa:
            self._desenhar_disco(disco)
        self.raiz.show_all()

    def _desenhar_disco(self, disco) -> None:
        linha = caixa_h(16)
        linha.get_style_context().add_class("moa-cartao")
        linha.pack_start(capa_do_disco(self.ctx, disco, 84), False, False, 0)
        linha.pack_start(rotulo(disco.title, "moa-forte"), True, True, 0)
        voltar = botao("Colocar de volta na estante", "moa-pri",
                       ao_clicar=lambda d=disco: self._colocar_de_volta(d))
        linha.pack_start(voltar, False, False, 0)
        linha.pack_start(botao("Apagar de vez…", ao_clicar=lambda d=disco: self._perguntar(d)),
                         False, False, 0)
        if self.primeiro_botao is None:
            self.primeiro_botao = voltar
        self.raiz.pack_start(linha, False, False, 0)
        if self.confirmando == disco.id:
            self.raiz.pack_start(self._pergunta(disco), False, False, 0)

    def _pergunta(self, disco) -> Gtk.Widget:
        montado = eh_disco_montado(disco.id)
        consequencia = ("O disco montado será desfeito. As músicas dos outros discos não são apagadas."
                        if montado else
                        "Os arquivos de música deste disco também serão apagados do computador "
                        "e não voltam.")
        caixa = caixa_v(10)
        caixa.get_style_context().add_class("moa-perigo-caixa")
        caixa.pack_start(rotulo(f"Apagar “{disco.title}” de vez? {consequencia}", "moa-forte"),
                         False, False, 0)
        botoes = caixa_h(12)
        manter = botao("Manter o disco", "moa-pri", "moa-grande", ao_clicar=self._manter)
        botoes.pack_start(manter, False, False, 0)
        botoes.pack_start(botao("Sim, apagar de vez", "moa-grande", "moa-perigo",
                                ao_clicar=lambda d=disco: self._apagar(d)), False, False, 0)
        caixa.pack_start(botoes, False, False, 0)
        self.primeiro_botao = manter                 # o foco vai para o lado seguro
        return caixa

    # -- ações -------------------------------------------------------------------------------

    def _perguntar(self, disco) -> None:
        self.ctx.session.acao()
        self.confirmando = disco.id
        self.atualizar()

    def _manter(self) -> None:
        self.ctx.session.acao()
        self.confirmando = None
        self.atualizar()

    def _colocar_de_volta(self, disco) -> None:
        ctx = self.ctx
        ctx.session.acao()
        self.confirmando = None
        box.colocar_de_volta(ctx.banco, disco.id)
        ctx.recarregar()
        ctx.session.mostrar_aviso(f"Coloquei “{disco.title}” de volta na estante.")

    def _apagar(self, disco) -> None:
        ctx = self.ctx
        ctx.session.acao()
        self.confirmando = None
        try:
            resultado = box.apagar_de_vez(ctx.banco, disco, ctx.pasta_musica)
        except Exception:                              # nunca assusta o idoso com um erro técnico
            log.exception("erro inesperado ao apagar de vez")
            ctx.session.mostrar_aviso(MSG_FALHA_AO_APAGAR)
            return
        ctx.esquecer_arquivos_apagados()
        ctx.recarregar()
        if resultado.apagou_tudo:
            ctx.session.mostrar_aviso(f"Apaguei “{disco.title}” de vez.")
        else:
            ctx.session.mostrar_aviso(MSG_FALHA_AO_APAGAR)
