# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Enfeites desenhados por cima de painéis que já existem: os parafusos dos cantos (ADR-0024).

`instalar_parafusos` liga um desenho extra a um widget, sem criar widgets novos. É como
`elemento.addEventListener("paint", ...)` num canvas: depois que o GTK desenha o painel, a
função roda e põe quatro parafusos nos cantos. Cada parafuso vem do `CACHE` (desenhado uma vez
por tamanho, giro da fenda e paleta), então redesenhar o painel não custa quase nada.
"""

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.ui import cairo_pecas, theme  # noqa: E402

DIAMETRO_PX = 16
MARGEM_PX = 6


def instalar_parafusos(painel: Gtk.Widget, diametro: int = DIAMETRO_PX, margem: int = MARGEM_PX) -> None:
    """Põe um parafuso em cada canto do `painel`, dentro da margem (o conteúdo não é coberto)."""
    painel.connect_after("draw", _desenhar_parafusos, diametro, margem)


def _desenhar_parafusos(painel: Gtk.Widget, cr, diametro: int, margem: int) -> bool:
    largura, altura = painel.get_allocated_width(), painel.get_allocated_height()
    minimo = 2 * (diametro + margem)               # cabem dois parafusos e as margens?
    if largura < minimo or altura < minimo:
        return False
    paleta = theme.paleta_atual()
    cantos = ((margem, margem), (largura - margem - diametro, margem),
              (margem, altura - margem - diametro), (largura - margem - diametro, altura - margem - diametro))
    for giro, (x, y) in enumerate(cantos):          # a fenda de cada parafuso está num ângulo
        peca = cairo_pecas.CACHE.obter("parafuso", diametro, diametro, paleta, giro,
                                       cairo_pecas.desenhar_parafuso)
        cr.set_source_surface(peca, x, y)
        cr.paint()
    return False
