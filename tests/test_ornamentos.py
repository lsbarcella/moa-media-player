# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes dos parafusos que enfeitam os cantos dos painéis (U3, ADR-0024)."""

import gi
import pytest

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.ui import cairo_pecas, ornamentos, theme  # noqa: E402
from tests.ui_ajuda import girar, tem_display  # noqa: E402

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


def _janela_com_painel():
    painel = Gtk.Box()
    painel.set_size_request(300, 200)
    ornamentos.instalar_parafusos(painel)
    janela = Gtk.OffscreenWindow()
    janela.add(painel)
    janela.show_all()
    girar(0.3)                                           # deixa o GTK dimensionar e mostrar
    return janela, painel


def test_desenhar_o_painel_pinta_quatro_parafusos_e_usa_o_cache():
    cairo_pecas.CACHE.limpar()
    janela, _ = _janela_com_painel()
    for _ in range(3):
        janela.get_pixbuf()                              # força um desenho novo a cada vez
    # 4 parafusos, cada um com seu giro da fenda, desenhados uma vez só
    assert len(cairo_pecas.CACHE) == 4
    janela.destroy()


def test_trocar_a_paleta_gera_desenhos_novos_sem_reiniciar_nada():
    cairo_pecas.CACHE.limpar()
    theme.definir_paleta_atual("normal")
    janela, painel = _janela_com_painel()
    janela.get_pixbuf()
    antes = len(cairo_pecas.CACHE)
    theme.definir_paleta_atual("azul-amarelo")
    painel.queue_draw()
    girar(0.3)
    janela.get_pixbuf()
    assert len(cairo_pecas.CACHE) == antes * 2
    theme.definir_paleta_atual("normal")
    janela.destroy()
