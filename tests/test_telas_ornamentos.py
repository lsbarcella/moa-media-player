# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Os parafusos aparecem nas placas da Estante, no Aparelho de CD e no painel do "+" (U7)."""

import gi
import pytest

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.session import Tela
from moa.ui import cairo_pecas
from tests.test_ui_smoke import app, montar, musica  # noqa: E402,F401  (fixtures)
from tests.ui_ajuda import desenhar, tem_display

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


def _lados_dos_parafusos():
    return {k[1] for k in cairo_pecas.CACHE.chaves() if k[0] == "parafuso"}


def test_a_estante_tem_placas_de_prata_com_parafusos_pequenos(app, tmp_path):
    ctx, conteudo = app
    cairo_pecas.CACHE.limpar()
    ctx.session.ir_para(Tela.ESTANTE)
    desenhar(conteudo, tmp_path / "estante.png")
    assert 10 in _lados_dos_parafusos()


def test_o_aparelho_de_cd_tem_parafusos_nos_cantos(app, tmp_path):
    ctx, conteudo = app
    cairo_pecas.CACHE.limpar()
    ctx.session.ir_para(Tela.APARELHO_DE_CD)
    desenhar(conteudo, tmp_path / "cd.png")
    assert 16 in _lados_dos_parafusos()


def test_a_barra_de_rolagem_da_janela_fica_sempre_visivel(app):
    ctx, conteudo = app
    rolagens = []

    def achar(w):
        if isinstance(w, Gtk.ScrolledWindow):
            rolagens.append(w)
        if isinstance(w, Gtk.Container):
            w.foreach(achar)
    achar(conteudo.raiz)
    assert rolagens and all(not r.get_overlay_scrolling() for r in rolagens)
