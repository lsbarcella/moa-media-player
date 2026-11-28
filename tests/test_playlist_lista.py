# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""A lista da tela "Criar uma playlist": marcar muda só uma linha e a lista vem em pedaços."""

import pytest

from moa.core.session import Tela
from moa.ui.playlist_view import MAXIMO_NA_LISTA
from tests.test_ui_smoke import montar
from tests.ui_ajuda import girar, tem_display, textos

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


@pytest.fixture
def com_muitas(tmp_path, make_track):
    raiz = tmp_path / "grande"
    for n in range(1, MAXIMO_NA_LISTA + 21):
        make_track(raiz / "MIX", f"{n:03d}.mp3", title=f"Musica {n:03d}", album="MIX",
                   artist="Ana", albumartist="Ana", tracknumber=str(n))
    ctx, conteudo = montar(tmp_path, raiz)
    ctx.session.ir_para(Tela.PLAYLIST)
    yield ctx, conteudo, conteudo.telas[Tela.PLAYLIST]
    ctx.encerrar()
    ctx.banco.close()


def _esperar(visao, quantas):
    for _ in range(300):
        if len(visao._linhas) >= quantas and not visao._construtor_da_lista.pendente:
            return
        girar(0.05)
    raise AssertionError(f"a lista parou em {len(visao._linhas)} de {quantas}")


def test_a_lista_vem_em_pedacos_e_respeita_o_limite(com_muitas):
    ctx, conteudo, visao = com_muitas
    assert 30 <= len(visao._linhas) < MAXIMO_NA_LISTA + 1          # as primeiras já estão na tela
    _esperar(visao, MAXIMO_NA_LISTA)
    assert len(visao._linhas) == MAXIMO_NA_LISTA
    aviso_do_limite = [t for t in textos(visao._area_da_lista) if t.startswith("Mostrando as primeiras")]
    assert len(aviso_do_limite) == 1                                 # a nota vem depois das linhas


def test_marcar_muda_so_a_linha_e_nao_refaz_a_lista(com_muitas):
    ctx, conteudo, visao = com_muitas
    _esperar(visao, MAXIMO_NA_LISTA)
    caminho = list(visao._linhas)[5]
    outra = list(visao._linhas)[6]
    antes = dict(visao._linhas)
    visao._linhas[caminho][0].clicked()
    assert visao._linhas == antes                                    # os mesmos widgets
    botao_, sinal, etiqueta = visao._linhas[caminho]
    assert sinal.get_text() == "✓" and etiqueta.get_text() == "Marcada"
    assert botao_.get_style_context().has_class("moa-marcada")
    assert visao._linhas[outra][1].get_text() == " "
    assert "1 música escolhida" in textos(visao._area_do_cartao)
    botao_.clicked()                                                  # desmarcar
    assert sinal.get_text() == " " and etiqueta.get_text() == "" and not botao_.get_style_context().has_class("moa-marcada")
    assert "Nenhuma música escolhida" in textos(visao._area_do_cartao)


def test_marcar_antes_da_lista_completar_nao_quebra(com_muitas):
    ctx, conteudo, visao = com_muitas
    primeira = list(visao._linhas)[0]
    visao._linhas[primeira][0].clicked()
    _esperar(visao, MAXIMO_NA_LISTA)
    assert visao._linhas[primeira][1].get_text() == "✓"
    assert len(ctx.rascunho.marcadas) == 1


def test_digitar_depressa_cancela_a_lista_anterior(com_muitas):
    ctx, conteudo, visao = com_muitas
    anterior = visao._construtor_da_lista
    visao.campo_de_busca.set_text("Musica 1")
    assert visao._construtor_da_lista is not anterior and not anterior.pendente
    _esperar(visao, len(visao._linhas))
    achadas = [t for t in textos(visao._area_da_lista) if t.startswith("Musica")]
    assert achadas and all(t.startswith("Musica 1") for t in achadas)


def test_a_marca_sobrevive_a_uma_nova_busca(com_muitas):
    ctx, conteudo, visao = com_muitas
    caminho = list(visao._linhas)[0]
    visao._linhas[caminho][0].clicked()
    visao.campo_de_busca.set_text("Musica 00")
    _esperar(visao, 1)
    visao.campo_de_busca.set_text("")
    _esperar(visao, MAXIMO_NA_LISTA)
    assert visao._linhas[caminho][1].get_text() == "✓"
