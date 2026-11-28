# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes do botão de volume e da escala do visor, desenhados em Cairo (U5, ADR-0024)."""

import gi
import pytest

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from moa.core.session import Tela  # noqa: E402
from moa.ui import cairo_pecas, instrumentos, theme  # noqa: E402
from tests.test_ui_smoke import app, montar, musica  # noqa: E402,F401  (fixtures)
from tests.ui_ajuda import girar, tem_display, textos  # noqa: E402

# ---- geometria pura: não precisa de tela -----------------------------------------------------


def test_o_botao_aponta_para_a_esquerda_no_zero_e_para_a_direita_no_dez():
    assert instrumentos.angulo_do_botao(0, 10) == -instrumentos.VARREDURA_GRAUS / 2
    assert instrumentos.angulo_do_botao(10, 10) == instrumentos.VARREDURA_GRAUS / 2
    assert instrumentos.angulo_do_botao(5, 10) == 0


def test_cada_degrau_gira_o_mesmo_tanto():
    angulos = [instrumentos.angulo_do_botao(k, 10) for k in range(11)]
    passos = {round(b - a, 6) for a, b in zip(angulos, angulos[1:])}
    assert len(passos) == 1 and passos.pop() > 0


def test_degrau_fora_da_faixa_e_corrigido():
    assert instrumentos.angulo_do_botao(-3, 10) == instrumentos.angulo_do_botao(0, 10)
    assert instrumentos.angulo_do_botao(99, 10) == instrumentos.angulo_do_botao(10, 10)


# ---- widgets: precisam de tela ---------------------------------------------------------------

com_tela = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


def _mostrar(widget, w=200, h=200):
    janela = Gtk.OffscreenWindow()
    janela.set_size_request(w, h)
    janela.add(widget)
    janela.show_all()
    girar(0.3)
    return janela


@com_tela
def test_o_botao_de_volume_nao_e_clicavel_nem_arrastavel_nem_focavel():
    botao = instrumentos.BotaoDeVolume(10)
    assert not botao.get_can_focus()
    assert not (botao.get_events() & (Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.POINTER_MOTION_MASK))


@com_tela
def test_o_botao_de_volume_so_redesenha_quando_o_degrau_muda():
    botao = instrumentos.BotaoDeVolume(10)
    janela = _mostrar(botao)
    botao.definir_degrau(4)
    assert botao.degrau == 4
    assert botao.definir_degrau(4) is False          # igual: nada a redesenhar
    assert botao.definir_degrau(5) is True
    janela.destroy()


@com_tela
def test_o_botao_de_volume_usa_o_cache_em_vez_de_redesenhar_as_pecas():
    cairo_pecas.CACHE.limpar()
    botao = instrumentos.BotaoDeVolume(10)
    janela = _mostrar(botao)
    botao.definir_degrau(6)
    girar(0.2)
    janela.get_pixbuf()
    depois_do_primeiro = len(cairo_pecas.CACHE)
    for _ in range(5):
        botao.queue_draw()
        girar(0.1)
        janela.get_pixbuf()
    assert len(cairo_pecas.CACHE) == depois_do_primeiro
    janela.destroy()


@com_tela
@pytest.mark.parametrize("paleta", list(theme.PALETAS))
def test_os_instrumentos_desenham_em_toda_paleta(paleta):
    theme.definir_paleta_atual(paleta)
    for widget, w, h in ((instrumentos.BotaoDeVolume(10), 160, 160), (instrumentos.LinhaDeProgresso(lambda f: None), 400, 80)):
        janela = _mostrar(widget, w, h)
        assert janela.get_pixbuf() is not None
        janela.destroy()
    theme.definir_paleta_atual("normal")


@com_tela
def test_no_radio_o_volume_gira_e_a_barra_mostra_o_andamento(app):
    ctx, conteudo = app
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    ctx.session.ir_para(Tela.RADIO)
    p = conteudo.telas[Tela.RADIO]._p
    ctx.player.definir_degrau_de_volume(3)
    ctx.radio.volume_mais()
    assert p.botao_volume.degrau == ctx.player.degrau_de_volume
    assert f"Volume: {ctx.player.degrau_de_volume} de 10" in textos(p.corpo)
    assert p.progresso.barra.fracao == 0.0 or 0.0 <= p.progresso.barra.fracao <= 1.0
    assert p.progresso.rotulo_atual.get_text()                 # o tempo decorrido está escrito


@com_tela
def test_as_teclas_de_volume_so_tem_o_simbolo_e_um_nome_acessivel(app):
    ctx, conteudo = app
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    ctx.session.ir_para(Tela.RADIO)
    p = conteudo.telas[Tela.RADIO]._p
    for tecla, nome in ((p.menos, "Mais baixo"), (p.mais, "Mais alto")):
        assert textos(tecla) == []                              # nenhum texto visível
        assert tecla.get_accessible().get_name() == nome        # mas um leitor de tela diz o nome
        assert tecla.get_tooltip_text() == nome
        # o símbolo é uma imagem com pelo menos o tamanho do alvo mínimo
        assert tecla.get_preferred_height()[0] >= theme.ALVO_MINIMO_PX


@com_tela
def test_volume_no_minimo_e_no_maximo_apagam_a_tecla_e_dizem_o_motivo(app):
    ctx, conteudo = app
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    ctx.session.ir_para(Tela.RADIO)
    p = conteudo.telas[Tela.RADIO]._p
    ctx.player.definir_degrau_de_volume(10)
    ctx.radio.volume_mais()
    assert p.mais.get_style_context().has_class("moa-inativo")
    assert p.mais.get_accessible().get_name() == "Volume no máximo"
    ctx.player.definir_degrau_de_volume(5)
    ctx.radio.volume_mais()
    assert not p.mais.get_style_context().has_class("moa-inativo")
    assert p.mais.get_accessible().get_name() == "Mais alto"
