# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""A lista de músicas do rádio não pode ser refeita a cada clique de volume.

Num disco com centenas de músicas (a coleção do usuário tem uma pasta com 371),
refazer a lista a cada clique travava a tela. Aqui se confere QUANDO ela é refeita.
"""

import pytest

from moa.core.session import Tela
from moa.ui import widgets
from tests.test_ui_smoke import app, musica, montar  # noqa: F401  (fixtures)
from tests.ui_ajuda import tem_display, textos

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


def _abrir_no_radio(ctx):
    ctx.radio.abrir_disco(ctx.discos[0])
    ctx.session.ir_para(Tela.RADIO)


def test_volume_nao_refaz_a_lista(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    ctx.radio.volume_mais()
    ctx.radio.volume_menos()
    ctx.radio.alternar_voz_mais_clara()
    assert visao._lista is antes
    assert antes.get_parent() is not None        # e continua dentro da tela


def _linha_com_a_marca(visao):
    """Índices das músicas cuja linha mostra "Tocando agora" ou "Parado aqui"."""
    return [i for i, (_moldura, nomes) in enumerate(visao._linhas)
            if {"Tocando agora", "Parado aqui"} & set(textos(nomes))]


def test_trocar_de_faixa_move_a_marca_sem_refazer_a_lista(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    assert _linha_com_a_marca(visao) == [0]
    ctx.radio.proxima()
    assert visao._lista is antes
    assert _linha_com_a_marca(visao) == [1]
    ctx.radio.tocar_faixa(2)
    assert _linha_com_a_marca(visao) == [2]
    ctx.radio.anterior()
    assert _linha_com_a_marca(visao) == [1]


def test_pausar_troca_o_texto_da_marca_sem_refazer_a_lista(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    vistos = set()
    for _ in range(2):
        ctx.radio.alternar()
        esperado = "Tocando agora" if ctx.radio.tocando else "Parado aqui"
        marca = [t for t in textos(visao._lista) if t in {"Tocando agora", "Parado aqui"}]
        assert marca == [esperado]
        vistos.add(esperado)
    assert vistos == {"Tocando agora", "Parado aqui"}      # o texto mesmo mudou
    assert visao._lista is antes


def test_a_linha_atual_fica_destacada_so_nela(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    ctx.radio.proxima()
    destacadas = [i for i, (moldura, _n) in enumerate(visao._linhas)
                  if moldura.get_style_context().has_class("moa-agora")]
    assert destacadas == [1]


def test_trocar_de_disco_refaz_a_lista(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    ctx.radio.abrir_disco(ctx.discos[1])
    assert visao._lista is not antes
    assert ctx.discos[1].tracks[0].title in textos(visao._lista)


def test_mudar_a_colecao_refaz_a_lista(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    ctx.recarregar()
    conteudo.redesenhar()
    assert visao._lista is not antes


def test_aviso_refaz_a_lista(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    ctx.session.mostrar_aviso("Teste", ancora=str(ctx.discos[0].tracks[0].path))
    assert visao._lista is not antes
    assert "Teste" in textos(visao._lista)


def test_icone_igual_so_e_convertido_uma_vez():
    widgets._cache_de_icones.clear()
    widgets.icone("mais")
    widgets.icone("mais")
    widgets.icone("mais", "#FFFFFF", "#1E1913")
    assert len(widgets._cache_de_icones) == 2
