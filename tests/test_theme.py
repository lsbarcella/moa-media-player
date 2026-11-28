# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes do tema (M3): contraste de 7:1 e tamanhos mínimos."""

import re

import pytest

from moa.ui import theme


@pytest.mark.parametrize("paleta", list(theme.PALETAS))
def test_todo_par_de_texto_e_fundo_tem_contraste_de_7_para_1(paleta):
    ruins = [(t, f, round(theme.contraste(paleta, t, f), 2))
             for t, f in theme.PARES_DE_CONTRASTE
             if theme.contraste(paleta, t, f) < theme.CONTRASTE_MINIMO]
    assert not ruins, f"{paleta}: {ruins}"


def test_as_quatro_paletas_e_as_tres_letras_existem():
    assert list(theme.PALETAS) == ["normal", "vermelho-verde", "azul-amarelo", "preto-e-branco"]
    assert list(theme.ESCALAS) == ["normal", "grande", "maior"]


def _tamanhos(css, propriedade):
    return [int(v) for v in re.findall(rf"{propriedade}:\s*(\d+)px", css)]


@pytest.mark.parametrize("paleta", list(theme.PALETAS))
def test_na_escala_normal_nenhum_texto_tem_menos_de_20px_e_nenhum_botao_menos_de_64px(paleta):
    css = theme.gerar_css(paleta, "normal")
    assert min(_tamanhos(css, "font-size")) >= 20
    botoes = re.findall(r"button\.moa-\w+ \{[^}]*?min-height:\s*(\d+)px", css)
    assert botoes and min(int(b) for b in botoes) >= 64


def test_nas_escalas_grande_e_maior_a_letra_so_cresce():
    normal, grande, maior = (max(_tamanhos(theme.gerar_css("normal", e), "font-size"))
                             for e in ("normal", "grande", "maior"))
    assert normal < grande < maior
    base = lambda e: _tamanhos(theme.gerar_css("normal", e), "font-size")[0]
    assert base("normal") == 20 < base("grande") < base("maior")


def test_o_css_trocou_de_cor_ao_trocar_de_paleta():
    assert theme.gerar_css("normal") != theme.gerar_css("preto-e-branco")
    assert "#14407A" in theme.gerar_css("vermelho-verde")


def test_o_css_e_aceito_pelo_gtk():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    for paleta in theme.PALETAS:
        for letra in theme.ESCALAS:
            provedor = Gtk.CssProvider()
            provedor.load_from_data(theme.gerar_css(paleta, letra).encode("utf-8"))
