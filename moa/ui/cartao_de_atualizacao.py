# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""ATUALIZAÇÃO DE TESTE (TEMPORÁRIA, REMOVER ANTES DA VERSÃO FINAL, ADR-0020).

O cartão que mostra o estado da atualização e os botões. Aparece em Configurações
(sempre) e na Estante (só quando há algo a fazer: versão nova, instalando, pronto).
"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.atualizacao_de_teste import Momento  # noqa: E402
from moa.core.contexto import Contexto  # noqa: E402
from moa.ui.widgets import botao, caixa_h, caixa_v, rotulo  # noqa: E402

MOMENTOS_COM_ALGO_A_FAZER = {Momento.HA_NOVA, Momento.BAIXANDO, Momento.PRONTO}


def deve_aparecer_na_estante(ctx: Contexto) -> bool:
    return ctx.atualizacao.habilitada and ctx.atualizacao.momento in MOMENTOS_COM_ALGO_A_FAZER


def cartao_de_atualizacao(ctx: Contexto) -> Gtk.Widget:
    a = ctx.atualizacao
    cartao = caixa_v(10)
    cartao.get_style_context().add_class("moa-cartao")
    cartao.pack_start(rotulo("Atualização do app (versão de teste)", "moa-grande"), False, False, 0)
    cartao.pack_start(rotulo(a.frase(), "moa-forte"), False, False, 0)
    cartao.pack_start(rotulo(a.versao_em_texto(), "moa-nota"), False, False, 0)

    linha = caixa_h(12)
    if a.momento == Momento.HA_NOVA:
        linha.pack_start(botao("Atualizar agora", "moa-pri", ao_clicar=lambda: _fazer(ctx, a.instalar)),
                         False, False, 0)
    elif a.momento == Momento.PRONTO:
        linha.pack_start(botao("Abrir de novo agora", "moa-pri", ao_clicar=lambda: _reiniciar(ctx)),
                         False, False, 0)
    elif not a.ocupada:
        linha.pack_start(botao("Procurar versão nova", ao_clicar=lambda: _fazer(ctx, a.verificar)),
                         False, False, 0)
    if a.tem_versao_anterior and not a.ocupada and a.momento != Momento.PRONTO:
        linha.pack_start(botao("Voltar à versão anterior",
                               ao_clicar=lambda: _fazer(ctx, a.voltar_a_anterior)), False, False, 0)
    cartao.pack_start(linha, False, False, 0)
    return cartao


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
