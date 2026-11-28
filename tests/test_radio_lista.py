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


def test_trocar_de_faixa_atualiza_o_tocando_agora(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    ctx.radio.proxima()
    assert visao._lista is not antes
    assert any("Parado aqui" in t or "Tocando agora" in t for t in textos(visao._lista))


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
