# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes da capa em caixa de CD: moldura, lombada com dobradiças e reflexo só na moldura (U6)."""

from pathlib import Path

import cairo
import gi
import pytest

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.models import Album, Track  # noqa: E402
from moa.ui import cairo_pecas, theme  # noqa: E402
from moa.ui.widgets import Capa  # noqa: E402
from tests.ui_ajuda import girar, tem_display  # noqa: E402

LADOS = (96, 120, 160, 200)


@pytest.mark.parametrize("lado", LADOS)
def test_a_arte_e_quadrada_e_cabe_dentro_da_moldura_e_ao_lado_da_lombada(lado):
    g = cairo_pecas.geometria_da_caixa(lado)
    assert g.arte_lado > 0 and g.arte_lado >= lado * 0.6
    assert g.arte_x >= g.lombada                                  # a arte começa depois da lombada
    assert g.arte_x + g.arte_lado <= lado - g.quadro              # e termina antes da moldura da direita
    assert g.arte_y >= g.quadro and g.arte_y + g.arte_lado <= lado - g.quadro


@pytest.mark.parametrize("paleta", list(theme.PALETAS))
@pytest.mark.parametrize("lado", LADOS)
def test_a_caixa_deixa_o_miolo_transparente_entao_o_reflexo_nunca_cobre_a_arte(paleta, lado):
    sup = cairo.ImageSurface(cairo.FORMAT_ARGB32, lado, lado)
    cairo_pecas.desenhar_caixa_de_cd(cairo.Context(sup), lado, lado, paleta, 0)
    g = cairo_pecas.geometria_da_caixa(lado)
    dados = bytes(sup.get_data())
    stride = sup.get_stride()
    for y in range(g.arte_y, g.arte_y + g.arte_lado):
        for x in range(g.arte_x, g.arte_x + g.arte_lado):
            assert dados[y * stride + x * 4 + 3] == 0, (x, y)     # alfa 0: nada sobre a arte


@pytest.mark.parametrize("paleta", list(theme.PALETAS))
def test_a_caixa_pinta_moldura_e_lombada(paleta):
    lado = 120
    sup = cairo.ImageSurface(cairo.FORMAT_ARGB32, lado, lado)
    cairo_pecas.desenhar_caixa_de_cd(cairo.Context(sup), lado, lado, paleta, 0)
    dados = bytes(sup.get_data())
    stride = sup.get_stride()
    g = cairo_pecas.geometria_da_caixa(lado)
    assert dados[(lado // 2) * stride + (g.lombada // 2) * 4 + 3] > 0       # lombada
    assert dados[(g.quadro // 2) * stride + (lado // 2) * 4 + 3] > 0        # moldura de cima


def _disco(titulo="Aqui vai um título longo de disco"):
    return Album(folder=Path("/x"), title=titulo, artist="Fulano",
                 tracks=(Track(path=Path("/x/1.mp3"), title="a", number=1),))


com_tela = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


def _pixel(pixbuf, x, y):
    n = pixbuf.get_n_channels()
    d = pixbuf.get_pixels()
    i = y * pixbuf.get_rowstride() + x * n
    return d[i], d[i + 1], d[i + 2]


@com_tela
@pytest.mark.parametrize("lado", (96, 160))
def test_a_capa_substituta_mostra_a_cor_pura_da_arte_sem_brilho_por_cima(lado):
    capa = Capa(_disco(), None, lado)
    janela = Gtk.OffscreenWindow()
    janela.add(capa)
    janela.show_all()
    girar(0.3)
    pix = janela.get_pixbuf()
    g = cairo_pecas.geometria_da_caixa(lado)
    fundo = capa._substituta.background.lstrip("#")
    esperado = tuple(int(fundo[i:i + 2], 16) for i in (0, 2, 4))
    # os quatro cantos da arte têm exatamente a cor da capa: nenhum reflexo por cima
    for x, y in ((g.arte_x + 1, g.arte_y + 1), (g.arte_x + g.arte_lado - 2, g.arte_y + 1),
                 (g.arte_x + 1, g.arte_y + g.arte_lado - 2), (g.arte_x + g.arte_lado - 2, g.arte_y + g.arte_lado - 2)):
        assert _pixel(pix, x, y) == esperado
    janela.destroy()


@com_tela
def test_a_caixa_vem_do_cache_e_nao_e_desenhada_de_novo():
    cairo_pecas.CACHE.limpar()
    capas = [Capa(_disco(f"Disco {n}"), None, 120) for n in range(6)]
    janela = Gtk.OffscreenWindow()
    caixa = Gtk.Box()
    for c in capas:
        caixa.pack_start(c, False, False, 0)
    janela.add(caixa)
    janela.show_all()
    girar(0.4)
    janela.get_pixbuf()
    caixas = [k for k in cairo_pecas.CACHE.chaves() if k[0] == "caixa"]
    assert len(caixas) == 1                          # seis capas, um só desenho da moldura
    janela.destroy()


@com_tela
def test_a_capa_continua_do_tamanho_pedido():
    capa = Capa(_disco(), None, 120)
    assert capa.get_size_request() == (120, 120)
