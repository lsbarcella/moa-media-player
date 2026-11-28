# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""A barra do rádio no pé das outras telas: visor, teclas e barra de progresso clicável (ADR-0026)."""

import gi
import pytest

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from moa.core.session import Tela  # noqa: E402
from moa.ui import instrumentos  # noqa: E402
from tests.test_ui_smoke import app, montar, musica  # noqa: E402,F401  (fixtures)
from tests.ui_ajuda import botao_com_texto, botoes, desenhar, girar, textos, tem_display  # noqa: E402

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


def _com_radio_tocando(app, tela=Tela.ESTANTE):
    ctx, conteudo = app
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    ctx.session.ir_para(tela)
    conteudo.redesenhar()
    return ctx, conteudo


# ---- a barra de progresso sozinha ----------------------------------------------------------

def test_a_barra_de_progresso_guarda_a_fracao_e_so_pede_desenho_se_mudou():
    barra = instrumentos.BarraDeProgresso(lambda f: None)
    assert barra.definir_fracao(0.4) is True
    assert barra.definir_fracao(0.4) is False
    assert barra.definir_fracao(7) is True and barra.fracao == 1.0       # corrigida para 0..1
    assert barra.definir_fracao(-3) is True and barra.fracao == 0.0


def test_o_alvo_da_barra_tem_pelo_menos_64_px_de_altura_e_nao_e_focavel():
    barra = instrumentos.BarraDeProgresso(lambda f: None)
    assert barra.get_size_request()[1] >= 64
    assert not barra.get_can_focus()                 # as setas do teclado são Anterior e Próxima


def test_clicar_na_barra_escolhe_a_fracao_do_ponto_clicado():
    escolhidas = []
    barra = instrumentos.BarraDeProgresso(escolhidas.append)
    janela = Gtk.OffscreenWindow()
    janela.set_size_request(400, 80)
    janela.add(barra)
    janela.show_all()
    girar(0.3)
    largura = barra.get_allocated_width()
    barra.escolher_em(largura * 0.25)
    barra.escolher_em(largura * 5)                   # além da ponta direita: 100%
    barra.escolher_em(-40)                           # antes da ponta esquerda: 0%
    assert escolhidas[0] == pytest.approx(0.25, abs=0.02)
    assert escolhidas[1:] == [1.0, 0.0]
    assert barra.fracao == 0.0                       # a barra já mostra o último ponto escolhido
    janela.destroy()


def test_um_clique_de_verdade_do_mouse_na_barra_chega_ate_a_acao():
    escolhidas = []
    barra = instrumentos.BarraDeProgresso(escolhidas.append)
    janela = Gtk.OffscreenWindow()
    janela.set_size_request(400, 80)
    janela.add(barra)
    janela.show_all()
    girar(0.3)
    evento = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS)
    evento.button.window = barra.get_window()
    evento.button.x = barra.get_allocated_width() / 2
    evento.button.y = 30
    evento.button.button = 1
    barra.event(evento)
    assert escolhidas and escolhidas[0] == pytest.approx(0.5, abs=0.05)
    janela.destroy()


# ---- a barra do rádio na janela --------------------------------------------------------------

def test_a_barra_mostra_visor_com_estado_musica_e_faixa(app):
    ctx, conteudo = _com_radio_tocando(app)
    t = textos(conteudo.mini)
    assert "PAUSADO" in t
    assert any("Faixa 1 de" in x for x in t)
    assert ctx.radio.visor().titulo in t


def test_a_barra_tem_anterior_tocar_proxima_e_abrir_o_radio(app):
    ctx, conteudo = _com_radio_tocando(app)
    nomes = [t for b in botoes(conteudo.mini) for t in textos(b)]
    for esperado in ("Anterior", "Tocar", "Próxima", "Abrir o rádio"):
        assert esperado in nomes, (esperado, nomes)


def test_as_teclas_da_barra_fazem_o_que_dizem(app):
    ctx, conteudo = _com_radio_tocando(app)
    ctx.radio.abrir_disco(ctx.discos[0], indice=1, tocar=False)
    conteudo.redesenhar()
    botao_com_texto(conteudo.mini, "Próxima").clicked()
    assert ctx.player.indice == 2
    botao_com_texto(conteudo.mini, "Anterior").clicked()
    assert ctx.player.indice == 1
    botao_com_texto(conteudo.mini, "Abrir o rádio").clicked()
    assert ctx.session.tela == Tela.RADIO


def test_tocar_e_pausar_trocam_na_barra_e_a_lampada_acompanha(app):
    ctx, conteudo = _com_radio_tocando(app)
    botao_com_texto(conteudo.mini, "Tocar").clicked()
    conteudo.redesenhar()
    assert "TOCANDO" in textos(conteudo.mini)
    assert "Pausar" in [t for b in botoes(conteudo.mini) for t in textos(b)]
    ctx.radio.alternar()
    conteudo.redesenhar()
    assert "PAUSADO" in textos(conteudo.mini)


def test_a_barra_some_na_tela_do_radio_e_sem_nada_tocando(app):
    ctx, conteudo = _com_radio_tocando(app)
    assert conteudo.mini.get_visible()
    ctx.session.ir_para(Tela.RADIO)
    conteudo.redesenhar()
    assert not conteudo.mini.get_visible()
    ctx.session.ir_para(Tela.ESTANTE)
    ctx.radio.guardar_o_disco_e_parar()
    conteudo.redesenhar()
    assert not conteudo.mini.get_visible()


def test_clicar_na_barra_de_progresso_da_janela_busca_no_rádio(app, monkeypatch, tmp_path):
    ctx, conteudo = _com_radio_tocando(app)
    desenhar(conteudo, tmp_path / "janela.png")           # a janela precisa estar na tela para ter tamanho
    pedidos = []
    monkeypatch.setattr(ctx.radio, "buscar_fracao", pedidos.append)
    barra = conteudo.barra_do_radio
    barra.escolher_em(barra.get_allocated_width() * 0.5)
    assert len(pedidos) == 1 and pedidos[0] == pytest.approx(0.5, abs=0.1)


def test_o_tempo_nas_pontas_acompanha_a_musica(app):
    ctx, conteudo = _com_radio_tocando(app)
    girar(0.3)
    conteudo.atualizar_progresso_do_mini()
    t = textos(conteudo.mini)
    assert any(":" in x and len(x) <= 5 for x in t)          # "0:00" e a duração


def test_a_dica_diz_em_texto_que_a_barra_e_clicavel(app):
    ctx, conteudo = _com_radio_tocando(app)
    assert any("Clique na barra" in x for x in textos(conteudo.mini))


def test_a_barra_em_letra_maior_desenha_sem_erro(app, tmp_path):
    ctx, conteudo = _com_radio_tocando(app)
    ctx.preferencias.mudar(letra="maior")
    conteudo.redesenhar()
    desenhar(conteudo, tmp_path / "maior.png")
