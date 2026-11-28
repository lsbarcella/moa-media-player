# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes das teclas travadas com lâmpada (U2, ADR-0024)."""

import gi
import pytest

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.session import Tela  # noqa: E402
from moa.ui.widgets import definir_estado_da_tecla, lampada_da_tecla, tecla_travavel  # noqa: E402
from tests.test_ui_smoke import app, montar, musica  # noqa: E402,F401  (fixtures)
from tests.ui_ajuda import botao_com_texto, botoes, textos, tem_display  # noqa: E402

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


def _tem(widget, classe):
    return widget.get_style_context().has_class(classe)


def test_tecla_travavel_desligada_fica_alta_e_com_lampada_apagada():
    t = tecla_travavel("Voz mais clara: desligada", False)
    assert not _tem(t, "moa-travada") and not _tem(lampada_da_tecla(t), "moa-acesa")


def test_ligar_baixa_a_tecla_e_acende_a_lampada_e_desligar_desfaz():
    t = tecla_travavel("Voz mais clara", False)
    definir_estado_da_tecla(t, True)
    assert _tem(t, "moa-travada") and _tem(lampada_da_tecla(t), "moa-acesa")
    definir_estado_da_tecla(t, False)
    assert not _tem(t, "moa-travada") and not _tem(lampada_da_tecla(t), "moa-acesa")


def test_a_tecla_travavel_sempre_tem_texto_e_o_clique_chama_a_acao():
    chamadas = []
    t = tecla_travavel("Voz mais clara", False, ao_clicar=lambda: chamadas.append(1))
    assert "Voz mais clara" in textos(t)
    t.clicked()
    assert chamadas == [1]


def test_voz_mais_clara_no_radio_baixa_e_acende_junto_com_o_texto(app):
    ctx, conteudo = app
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    ctx.session.ir_para(Tela.RADIO)
    tecla = botao_com_texto(conteudo.raiz, "Voz mais clara: desligada")
    assert not _tem(tecla, "moa-travada")
    tecla.clicked()
    tecla = botao_com_texto(conteudo.raiz, "Voz mais clara: ligada")
    assert _tem(tecla, "moa-travada") and _tem(lampada_da_tecla(tecla), "moa-acesa")
    tecla.clicked()
    assert not _tem(botao_com_texto(conteudo.raiz, "Voz mais clara: desligada"), "moa-travada")


def test_banco_de_teclas_das_configuracoes_so_uma_fica_baixada_por_grupo(app):
    """Apertar uma tecla do banco solta as outras: só a escolhida tem lâmpada acesa."""
    ctx, conteudo = app
    ctx.session.ir_para(Tela.CONFIGURACOES)
    raiz = conteudo.telas[Tela.CONFIGURACOES].raiz
    botao_com_texto(raiz, "Grande").clicked()
    escolhidas = [b for b in botoes(raiz) if _tem(b, "moa-escolhida")]
    letra = [b for b in escolhidas if "Grande" in textos(b)]
    assert len(letra) == 1
    for b in botoes(raiz):
        if "Normal" in textos(b) or "Maior" in textos(b):
            assert not _tem(b, "moa-escolhida")
