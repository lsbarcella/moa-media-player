# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes das peças desenhadas em Cairo e do cache de desenho (U4, ADR-0024)."""

import cairo
import pytest

from moa.ui import cairo_pecas, theme


def _superficie(w, h):
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)


def _pixels_pintados(sup):
    dados = bytes(sup.get_data())
    return sum(1 for i in range(3, len(dados), 4) if dados[i] > 0)


@pytest.mark.parametrize("peca", ["parafuso", "dobradica", "serrilha", "lente"])
@pytest.mark.parametrize("paleta", list(theme.PALETAS))
def test_toda_peca_desenha_alguma_coisa_em_toda_paleta(peca, paleta):
    sup = _superficie(48, 48)
    cr = cairo.Context(sup)
    getattr(cairo_pecas, f"desenhar_{peca}")(cr, 48, 48, paleta, estado=True)
    assert _pixels_pintados(sup) > 0


def test_o_parafuso_tem_fenda_e_a_fenda_muda_com_o_estado():
    a, b = _superficie(40, 40), _superficie(40, 40)
    cairo_pecas.desenhar_parafuso(cairo.Context(a), 40, 40, "normal", estado=0)
    cairo_pecas.desenhar_parafuso(cairo.Context(b), 40, 40, "normal", estado=1)
    assert bytes(a.get_data()) != bytes(b.get_data())      # a fenda gira: dá variedade


@pytest.mark.parametrize("peca", ["parafuso", "dobradica", "serrilha", "lente"])
def test_no_preto_e_branco_as_pecas_nao_tem_tom_de_prata_nem_de_metal(peca):
    """Só preto, branco e o cinza do contorno: os canais de cor ficam sempre próximos."""
    sup = _superficie(40, 40)
    getattr(cairo_pecas, f"desenhar_{peca}")(cairo.Context(sup), 40, 40, "preto-e-branco", estado=1)
    dados = bytes(sup.get_data())
    for i in range(0, len(dados), 4):
        if dados[i + 3] == 255:          # pixel opaco (BGRA)
            assert max(dados[i:i + 3]) - min(dados[i:i + 3]) <= 30


def test_o_cache_so_desenha_uma_vez_por_tamanho_estado_e_paleta():
    cache = cairo_pecas.CacheDeDesenho()
    chamadas = []

    def fazer(cr, w, h, paleta, estado):
        chamadas.append((w, h, paleta, estado))
        cairo_pecas.desenhar_parafuso(cr, w, h, paleta, estado)

    for _ in range(5):
        cache.obter("parafuso", 30, 30, "normal", 0, fazer)
    assert len(chamadas) == 1
    cache.obter("parafuso", 30, 30, "normal", 1, fazer)       # outro estado
    cache.obter("parafuso", 31, 30, "normal", 0, fazer)       # outro tamanho
    cache.obter("parafuso", 30, 30, "azul-amarelo", 0, fazer)  # outra paleta
    assert len(chamadas) == 4


def test_o_cache_tem_limite_e_descarta_o_mais_antigo():
    cache = cairo_pecas.CacheDeDesenho(limite=3)
    for tam in range(10, 16):
        cache.obter("parafuso", tam, tam, "normal", 0, cairo_pecas.desenhar_parafuso)
    assert len(cache) == 3


def test_paleta_atual_acompanha_o_que_aplicar_configurou():
    theme.definir_paleta_atual("azul-amarelo")
    assert theme.paleta_atual() == "azul-amarelo"
    theme.definir_paleta_atual("normal")
    assert theme.paleta_atual() == "normal"


def test_paleta_desconhecida_cai_na_normal():
    theme.definir_paleta_atual("não existe")
    assert theme.paleta_atual() == "normal"
