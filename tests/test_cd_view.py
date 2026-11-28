# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes da tela "Aparelho de CD", desenhada fora da tela (KTD15)."""

import pytest

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.aparelho import AparelhoDeCD, Momento  # noqa: E402
from moa.core.config import Preferencias  # noqa: E402
from moa.core.contexto import Contexto  # noqa: E402
from moa.core.db import Database  # noqa: E402
from moa.core.library import scan  # noqa: E402
from moa.core.session import Tela  # noqa: E402
from moa.ui import theme  # noqa: E402
from moa.ui.window import Conteudo  # noqa: E402
from tests.test_player import _sink_rapido  # noqa: E402
from tests.ui_ajuda import botao_com_texto, botoes, desenhar, girar, textos, tem_display  # noqa: E402

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


def _fonte(_n: int) -> str:
    return "audiotestsrc num-buffers=8 samplesperbuffer=1024"


def montar(tmp_path, make_track, com_discos=True):
    musica = tmp_path / "musica"
    musica.mkdir()
    if com_discos:
        for n in (1, 2):
            make_track(musica / "Ana Boleros", f"{n:02d}.mp3", title=f"Bolero {n}", album="Boleros",
                       artist="Ana", albumartist="Ana", tracknumber=str(n))
    banco = Database(tmp_path / "moa.db")
    prefs = Preferencias(tmp_path / "config.json")
    theme.aplicar(prefs.config.paleta, prefs.config.letra)
    ctx = Contexto(banco, prefs, musica, sink_factory=_sink_rapido,
                   pasta_miniaturas=tmp_path / "miniaturas")
    ctx.aparelho = AparelhoDeCD(musica, fonte=_fonte, contar_faixas=lambda: 3,
                                ejetar=lambda: True)
    conteudo = Conteudo(ctx)
    ctx.aparelho.ao_mudar(conteudo.redesenhar)
    ctx.definir_colecao(scan(musica), {})
    return ctx, conteudo


@pytest.fixture
def app(tmp_path, make_track):
    ctx, conteudo = montar(tmp_path, make_track)
    yield ctx, conteudo
    ctx.encerrar()
    ctx.banco.close()


def _tela(conteudo):
    return conteudo.telas[Tela.APARELHO_DE_CD].raiz


def test_o_botao_da_estante_abre_o_aparelho_com_caminho_de_volta(app):
    ctx, conteudo = app
    botao_com_texto(conteudo.telas[Tela.ESTANTE].raiz, "Colocar um disco").clicked()
    assert ctx.session.tela == Tela.APARELHO_DE_CD
    todos = textos(conteudo.raiz)
    assert "Aparelho de CD" in todos and "Voltar para a estante" in todos
    assert "ABRA A GAVETA E PONHA O CD" in textos(_tela(conteudo))


@pytest.mark.parametrize("momento, visor, botoes_esperados", [
    (Momento.INICIO, "ABRA A GAVETA E PONHA O CD", {"Abrir a gaveta", "Já coloquei o disco"}),
    (Momento.COPIANDO, "COPIANDO: lendo o disco…", {"Parar de copiar"}),
    (Momento.PRONTO, "PRONTO: 0 músicas", {"Ver o disco na estante", "Abrir a gaveta"}),
    (Momento.SEM_DISCO, "SEM DISCO NO APARELHO", {"Abrir a gaveta", "Tentar de novo"}),
    (Momento.FALHOU, "NÃO CONSEGUI COPIAR", {"Abrir a gaveta", "Tentar de novo"}),
])
def test_cada_momento_mostra_visor_e_botoes_com_texto(app, momento, visor, botoes_esperados, tmp_path):
    ctx, conteudo = app
    ctx.aparelho.momento = momento
    ctx.session.ir_para(Tela.APARELHO_DE_CD)
    raiz = _tela(conteudo)
    assert visor in textos(raiz)
    nomes = {t for b in botoes(raiz) for t in textos(b)}
    assert botoes_esperados <= nomes
    desenhar(conteudo, tmp_path / f"{momento.value}.png")
    for b in botoes(raiz):
        assert b.get_allocated_height() >= 64 or not b.get_mapped()


def test_copiar_ate_o_fim_e_ver_na_estante(app):
    ctx, conteudo = app
    ctx.session.ir_para(Tela.APARELHO_DE_CD)
    botao_com_texto(_tela(conteudo), "Já coloquei o disco").clicked()
    ctx.aparelho.thread.join(timeout=30)
    girar(0.2)
    assert ctx.aparelho.momento == Momento.PRONTO
    assert "PRONTO: 3 músicas" in textos(_tela(conteudo))
    botao_com_texto(_tela(conteudo), "Ver o disco na estante").clicked()
    assert ctx.session.tela == Tela.ESTANTE
    assert ctx.aparelho.momento == Momento.INICIO


def test_parar_de_copiar_volta_ao_comeco(app):
    ctx, conteudo = app
    ctx.aparelho = AparelhoDeCD(ctx.pasta_musica, fonte=_fonte, contar_faixas=lambda: 50)
    ctx.aparelho.ao_mudar(conteudo.redesenhar)
    ctx.session.ir_para(Tela.APARELHO_DE_CD)
    botao_com_texto(_tela(conteudo), "Já coloquei o disco").clicked()
    botao_com_texto(_tela(conteudo), "Parar de copiar").clicked()
    ctx.aparelho.thread.join(timeout=30)
    assert ctx.aparelho.momento == Momento.INICIO


def test_gaveta_que_nao_abre_da_uma_frase_calma(app):
    ctx, conteudo = app
    ctx.aparelho = AparelhoDeCD(ctx.pasta_musica, ejetar=lambda: False)
    ctx.session.ir_para(Tela.APARELHO_DE_CD)
    botao_com_texto(_tela(conteudo), "Abrir a gaveta").clicked()
    assert any("Não consegui abrir a gaveta" in t for t in textos(conteudo.raiz))


def test_estante_mostra_ver_a_copia_enquanto_copia(app):
    ctx, conteudo = app
    ctx.aparelho.momento = Momento.COPIANDO
    conteudo.redesenhar()
    assert any("Ver a cópia do disco" in textos(b) for b in botoes(conteudo.telas[Tela.ESTANTE].raiz))


def test_estante_vazia_ainda_tem_o_botao_para_colocar_um_disco(tmp_path, make_track):
    ctx, conteudo = montar(tmp_path, make_track, com_discos=False)
    try:
        assert any("Colocar um disco" in textos(b) for b in botoes(conteudo.telas[Tela.ESTANTE].raiz))
    finally:
        ctx.encerrar()
        ctx.banco.close()
