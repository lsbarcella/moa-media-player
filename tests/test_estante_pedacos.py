# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""A Estante só é refeita quando algo que ela mostra muda, e discos demais vêm em pedaços."""

import pytest

from moa.core.session import Tela
from tests.test_ui_smoke import montar
from tests.ui_ajuda import girar, tem_display, textos, todos_os_widgets

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


@pytest.fixture
def estante_cheia(tmp_path, make_track):
    raiz = tmp_path / "estante"
    for n in range(1, 61):
        make_track(raiz / f"Disco {n:02d}", "01.mp3", title=f"Musica {n}", album=f"Disco {n:02d}",
                   artist="Ana", albumartist="Ana", tracknumber="1")
    ctx, conteudo = montar(tmp_path, raiz)
    yield ctx, conteudo, conteudo.telas[Tela.ESTANTE]
    ctx.encerrar()
    ctx.banco.close()


def _discos_na_tela(visao):
    return [t for t in textos(visao.raiz) if t.startswith("Disco ")]


def _esperar(visao):
    for _ in range(300):
        if not any(c.pendente for c in visao._construtores):
            return
        girar(0.05)
    raise AssertionError("a estante não terminou de ser montada")


def test_estante_grande_mostra_os_primeiros_e_completa(estante_cheia):
    ctx, conteudo, visao = estante_cheia
    assert 24 <= len(_discos_na_tela(visao)) <= 60
    _esperar(visao)
    nomes = _discos_na_tela(visao)
    assert len(nomes) == 60 and "Disco 60" in nomes


def test_nao_refaz_a_estante_quando_nada_mudou(estante_cheia):
    ctx, conteudo, visao = estante_cheia
    _esperar(visao)
    filhos = list(visao.raiz.get_children())
    for _ in range(5):
        conteudo.redesenhar()
    assert list(visao.raiz.get_children()) == filhos           # os mesmos widgets


def test_refaz_quando_a_colecao_muda(estante_cheia):
    ctx, conteudo, visao = estante_cheia
    _esperar(visao)
    filhos = list(visao.raiz.get_children())
    ctx.recarregar()
    assert list(visao.raiz.get_children()) != filhos


def test_refaz_com_aviso_com_disco_no_radio_e_durante_a_copia(estante_cheia):
    ctx, conteudo, visao = estante_cheia
    _esperar(visao)
    filhos = list(visao.raiz.get_children())
    ctx.session.mostrar_aviso("Teste de aviso")
    assert "Teste de aviso" in textos(visao.raiz) and list(visao.raiz.get_children()) != filhos
    ctx.session.acao()
    assert "Teste de aviso" not in textos(visao.raiz)
    ctx.radio.abrir_disco(ctx.discos[0])
    ctx.session.voltar_para_a_estante()
    assert "Em uso no rádio" in textos(visao.raiz)
    from moa.core.aparelho import Momento
    ctx.aparelho.momento = Momento.COPIANDO
    conteudo.redesenhar()
    assert "Ver a cópia do disco" in [t for w in todos_os_widgets(visao.raiz) if hasattr(w, "get_label")
                                      for t in [w.get_label()] if t]


def test_o_foco_nao_pula_quando_a_estante_nao_mudou(estante_cheia):
    ctx, conteudo, visao = estante_cheia
    original = visao.foco_inicial
    entregues = []
    visao.foco_inicial = lambda: entregues.append(original()) or entregues[-1]
    conteudo.redesenhar()
    assert entregues[-1] is None
    ctx.session.ir_para(Tela.CAIXA)
    ctx.session.ir_para(Tela.ESTANTE)
    assert entregues[-1] is not None            # voltou para a estante: o foco vai ao botão principal
