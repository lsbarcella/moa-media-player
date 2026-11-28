# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""ATUALIZAÇÃO DE TESTE (TEMPORÁRIA, REMOVER ANTES DA VERSÃO FINAL, ADR-0020 e ADR-0024).

O cartão que mostra a atualização andando. Aparece em Configurações (sempre) e na Estante (só
quando há algo a fazer: versão nova, baixando, instalando, pronto).

Enquanto atualiza, o cartão mostra as três etapas ("✓ feita", "→ em andamento", "○ ainda não"),
o tamanho, uma barra de andamento e o botão "Reiniciar o Aplicativo", que já aparece mas só é
liberado quando a instalação termina. Os avanços do download e da instalação mudam só os textos
e a barra, no lugar, sem refazer o cartão.
"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.atualizacao_de_teste import Momento  # noqa: E402
from moa.core.contexto import Contexto  # noqa: E402
from moa.ui.widgets import botao, caixa_h, caixa_v, classe, rotulo, texto_de  # noqa: E402

MOMENTOS_COM_ALGO_A_FAZER = {Momento.HA_NOVA, Momento.BAIXANDO, Momento.INSTALANDO, Momento.PRONTO}
MOMENTOS_ATUALIZANDO = {Momento.BAIXANDO, Momento.INSTALANDO, Momento.PRONTO}
TEXTO_DO_BOTAO_DE_REINICIAR = "Reiniciar o Aplicativo"


def deve_aparecer_na_estante(ctx: Contexto) -> bool:
    return ctx.atualizacao.habilitada and ctx.atualizacao.momento in MOMENTOS_COM_ALGO_A_FAZER


class CartaoDeAtualizacao:
    def __init__(self, ctx: Contexto) -> None:
        self.ctx = ctx
        a = ctx.atualizacao
        self.raiz = caixa_v(10)
        self.raiz.get_style_context().add_class("moa-cartao")
        self.raiz.pack_start(rotulo("Atualização do app (versão de teste)", "moa-grande"), False, False, 0)
        self.raiz.pack_start(rotulo(a.frase(), "moa-forte"), False, False, 0)
        self._tamanho = rotulo("")
        self._tamanho.set_no_show_all(True)
        self.raiz.pack_start(self._tamanho, False, False, 0)

        self._etapas: list[Gtk.Label] = []
        self._area_das_etapas = caixa_v(4)
        for _ in range(3):
            etiqueta = rotulo("")
            self._area_das_etapas.pack_start(etiqueta, False, False, 0)
            self._etapas.append(etiqueta)
        self._area_das_etapas.set_no_show_all(True)
        self.raiz.pack_start(self._area_das_etapas, False, False, 0)

        self._barra = Gtk.ProgressBar()
        self._barra.get_style_context().add_class("moa-barra")
        self._barra.set_no_show_all(True)
        self.raiz.pack_start(self._barra, False, False, 0)

        self.raiz.pack_start(rotulo(a.versao_em_texto(), "moa-nota"), False, False, 0)
        self.botao_de_reiniciar: Gtk.Button | None = None
        self.raiz.pack_start(self._botoes(), False, False, 0)

        self._mostrar_o_andamento()
        a.ao_progredir(self._progresso)
        self.raiz.connect("destroy", lambda _w: a.tirar_ouvinte_do_progresso(self._progresso))

    # -- desenho ----------------------------------------------------------------------------

    def _botoes(self) -> Gtk.Widget:
        ctx, a = self.ctx, self.ctx.atualizacao
        linha = caixa_h(12)
        if a.momento == Momento.HA_NOVA:
            linha.pack_start(botao("Atualizar agora", "moa-pri", ao_clicar=lambda: _fazer(ctx, a.instalar)),
                             False, False, 0)
        elif a.momento in MOMENTOS_ATUALIZANDO:
            pronto = a.momento == Momento.PRONTO
            reiniciar = botao(TEXTO_DO_BOTAO_DE_REINICIAR, *(("moa-pri",) if pronto else ("moa-inativo",)),
                              ao_clicar=(lambda: _reiniciar(ctx)) if pronto else None)
            reiniciar.set_sensitive(pronto)         # só é liberado quando a instalação termina
            self.botao_de_reiniciar = reiniciar
            linha.pack_start(reiniciar, False, False, 0)
        elif not a.ocupada:
            linha.pack_start(botao("Procurar versão nova", ao_clicar=lambda: _fazer(ctx, a.verificar)),
                             False, False, 0)
        if a.tem_versao_anterior and not a.ocupada and a.momento not in MOMENTOS_ATUALIZANDO:
            linha.pack_start(botao("Voltar à versão anterior",
                                   ao_clicar=lambda: _fazer(ctx, a.voltar_a_anterior)), False, False, 0)
        return linha

    def _mostrar_o_andamento(self) -> None:
        a = self.ctx.atualizacao
        texto_de(self._tamanho, a.tamanho_em_texto())
        _mostrar(self._tamanho, bool(self._tamanho.get_text()))
        atualizando = a.momento in MOMENTOS_ATUALIZANDO
        _mostrar(self._area_das_etapas, atualizando)
        _mostrar(self._barra, atualizando)
        if not atualizando:
            return
        for etiqueta, (marca, texto) in zip(self._etapas, a.etapas()):
            texto_de(etiqueta, f"{marca}  {texto}")
            classe(etiqueta, "moa-forte", marca == "→")
        fracao = a.fracao()
        if fracao is None:
            self._barra.pulse()                     # baixando: o total não é conhecido antes
        else:
            self._barra.set_fraction(fracao)

    def _progresso(self) -> None:
        """Um avanço do download ou da instalação: muda só os textos e a barra."""
        self._mostrar_o_andamento()


def _mostrar(widget: Gtk.Widget, visivel: bool) -> None:
    """Mostra ou esconde uma parte do cartão, resistindo ao `show_all` da tela que o contém."""
    if visivel:
        widget.set_no_show_all(False)
        widget.show_all()
        widget.set_no_show_all(True)
    else:
        widget.hide()


def cartao_de_atualizacao(ctx: Contexto) -> Gtk.Widget:
    return CartaoDeAtualizacao(ctx).raiz


def _fazer(ctx: Contexto, acao) -> None:
    ctx.session.acao()
    acao()


def _reiniciar(ctx: Contexto) -> None:
    """Agenda a abertura de uma cópia nova e fecha a janela (o fechamento salva o estado)."""
    ctx.session.acao()
    ctx.atualizacao.preparar_reinicio()
    janela = Gtk.Application.get_default().get_active_window() if Gtk.Application.get_default() else None
    if janela is not None:
        janela.close()
