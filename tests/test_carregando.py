# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""O "carregando" da primeira leitura da pasta: andamento em palavras e aviso de demora."""

import pytest

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.covers import refresh_covers
from moa.core.db import Database
from moa.core.library import refresh_library
from moa.core.session import Tela
from moa.ui.loader import varrer
from moa.ui.shelf_view import TEXTO_CARREGANDO, TEXTO_DA_DEMORA
from tests.test_ui_smoke import montar, musica  # noqa: F401  (fixture)
from tests.ui_ajuda import girar, tem_display, textos, todos_os_widgets


def test_a_leitura_conta_as_musicas_que_ja_olhou(musica, tmp_path):
    contagem = []
    banco = Database(tmp_path / "a.db")
    discos = refresh_library(musica, banco, ao_progredir=contagem.append)
    assert contagem == list(range(1, 10))                  # 3 discos x 3 faixas
    contagem.clear()
    refresh_library(musica, banco, ao_progredir=contagem.append)    # com cache também conta
    assert contagem == list(range(1, 10))
    banco.close()


def test_as_capas_contam_discos_feitos_e_total(musica, tmp_path):
    banco = Database(tmp_path / "b.db")
    discos = refresh_library(musica, banco)
    passos = []
    refresh_covers(discos, banco, tmp_path / "mini", ao_progredir=lambda f, t: passos.append((f, t)))
    assert passos == [(1, 3), (2, 3), (3, 3)]
    banco.close()


def test_varrer_informa_as_duas_etapas(musica, tmp_path):
    eventos = []
    varrer(tmp_path / "c.db", musica, tmp_path / "mini", lambda e, f, t: eventos.append((e, f, t)))
    etapas = [e for e, _f, _t in eventos]
    assert etapas[0] == "musicas" and etapas[-1] == "capas"
    assert ("musicas", 9, None) in eventos and ("capas", 3, 3) in eventos


pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


@pytest.fixture
def lendo(tmp_path, musica):
    ctx, conteudo = montar(tmp_path, musica, carregado=False)
    yield ctx, conteudo
    ctx.encerrar()
    ctx.banco.close()


def _estante(conteudo):
    return conteudo.telas[Tela.ESTANTE]


def test_mostra_um_indicador_girando_e_o_texto(lendo):
    ctx, conteudo = lendo
    raiz = _estante(conteudo).raiz
    assert TEXTO_CARREGANDO in textos(raiz)
    espirais = [w for w in todos_os_widgets(raiz) if isinstance(w, Gtk.Spinner)]
    assert len(espirais) == 1 and espirais[0].get_property("active")


def test_o_andamento_aparece_em_palavras_simples(lendo):
    ctx, conteudo = lendo
    ctx.informar_progresso("musicas", 1, None)
    assert "Já olhei 1 música." in textos(_estante(conteudo).raiz)
    ctx.informar_progresso("musicas", 120, None)
    assert "Já olhei 120 músicas." in textos(_estante(conteudo).raiz)
    ctx.informar_progresso("capas", 12, 80)
    assert "Preparando as capas: 12 de 80." in textos(_estante(conteudo).raiz)


def test_o_andamento_muda_no_lugar_sem_refazer_a_estante(lendo):
    ctx, conteudo = lendo
    visao = _estante(conteudo)
    cartao_antes = visao._detalhe
    for n in range(1, 50):
        ctx.informar_progresso("musicas", n, None)
    assert visao._detalhe is cartao_antes


def test_so_avisa_da_demora_depois_de_5_segundos(lendo):
    ctx, conteudo = lendo
    ctx.informar_progresso("musicas", 3, None)
    assert TEXTO_DA_DEMORA not in textos(_estante(conteudo).raiz)
    ctx.inicio_da_leitura -= 6
    conteudo.tique(1)                                   # o relógio da janela confere o tempo
    assert TEXTO_DA_DEMORA in textos(_estante(conteudo).raiz)


def test_ao_terminar_o_carregando_some(lendo, musica):
    from moa.core.library import scan
    ctx, conteudo = lendo
    ctx.inicio_da_leitura -= 6
    conteudo.tique(1)
    ctx.definir_colecao(scan(musica), {})
    raiz = _estante(conteudo).raiz
    assert TEXTO_CARREGANDO not in textos(raiz) and TEXTO_DA_DEMORA not in textos(raiz)
    assert not [w for w in todos_os_widgets(raiz) if isinstance(w, Gtk.Spinner)]
    assert _estante(conteudo)._detalhe is None
    conteudo.tique(2)                                   # não quebra depois que acabou
