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
    conteudo.mostrar_o_progresso(True)
    desenhar(conteudo, tmp_path / "janela.png")           # a janela precisa estar na tela para ter tamanho
    pedidos = []
    monkeypatch.setattr(ctx.radio, "buscar_fracao", pedidos.append)
    barra = conteudo.barra_do_radio
    barra.escolher_em(barra.get_allocated_width() * 0.5)
    assert len(pedidos) == 1 and pedidos[0] == pytest.approx(0.5, abs=0.1)


def test_o_tempo_nas_pontas_acompanha_a_musica(app):
    ctx, conteudo = _com_radio_tocando(app)
    conteudo.mostrar_o_progresso(True)
    girar(0.4)
    conteudo.atualizar_progresso_do_mini()
    t = textos(conteudo._flutuante)
    assert any(":" in x and len(x) <= 5 for x in t)          # "0:00" e a duração


def test_a_barra_diz_que_e_clicavel_numa_dica_e_nao_gasta_uma_linha_inteira(app):
    ctx, conteudo = _com_radio_tocando(app)
    conteudo.mostrar_o_progresso(True)
    assert "Clique" in conteudo.barra_do_radio.get_tooltip_text()
    assert not any("Clique na barra" in x for x in textos(conteudo.mini))        # a linha de dica saiu (altura)


def test_a_barra_em_letra_maior_desenha_sem_erro(app, tmp_path):
    ctx, conteudo = _com_radio_tocando(app)
    ctx.preferencias.mudar(letra="maior")
    conteudo.redesenhar()
    desenhar(conteudo, tmp_path / "maior.png")


def _janela_1366(conteudo):
    janela = Gtk.OffscreenWindow()
    janela.set_size_request(1366, 768)
    janela.add(conteudo.raiz)
    janela.show_all()
    girar(0.6)
    return janela


def test_a_barra_recolhida_ocupa_pouco_mesmo_em_letra_maior(app):
    """Sem o mouse em cima, a barra é uma linha só: no máximo 18% de uma janela de 1366x768.

    O piso vem do alvo mínimo de 64 px das teclas, mais a borda, a bandeja e o fio de andamento.
    """
    ctx, conteudo = _com_radio_tocando(app)
    ctx.preferencias.mudar(letra="maior")
    conteudo.redesenhar()
    janela = _janela_1366(conteudo)
    altura = conteudo.mini.get_allocated_height()
    janela.remove(conteudo.raiz)
    janela.destroy()
    assert altura <= 768 * 0.18, altura


def test_abrir_o_radio_fica_na_linha_de_anterior_e_proxima_todo_para_a_direita(app):
    ctx, conteudo = _com_radio_tocando(app)
    janela = _janela_1366(conteudo)
    anterior = botao_com_texto(conteudo.mini, "Anterior")
    proxima = botao_com_texto(conteudo.mini, "Próxima")
    abrir = botao_com_texto(conteudo.mini, "Abrir o rádio")
    (_, y_ant), (x_abrir, y_abrir) = (anterior.translate_coordinates(janela, 0, 0),
                                       abrir.translate_coordinates(janela, 0, 0))
    x_prox = proxima.translate_coordinates(janela, 0, 0)[0] + proxima.get_allocated_width()
    direita_do_abrir = x_abrir + abrir.get_allocated_width()
    janela.remove(conteudo.raiz)
    janela.destroy()
    assert abs(y_ant - y_abrir) < 40                    # a mesma linha
    assert x_abrir > x_prox + 20                        # depois das três teclas
    assert direita_do_abrir >= 1366 - 40                # encostado na direita (menos a margem da barra)


def test_o_progresso_so_aparece_com_o_mouse_em_cima_e_some_depois_de_uma_pausa(app):
    ctx, conteudo = _com_radio_tocando(app)
    janela = _janela_1366(conteudo)
    assert not conteudo.progresso_visivel()
    conteudo.mostrar_o_progresso(True)
    girar(0.4)
    assert conteudo.progresso_visivel()
    conteudo.esconder_o_progresso_depois_de_uma_pausa()
    assert conteudo.progresso_visivel()                 # ainda: a pausa dá tempo de o mouse chegar na barra
    girar(0.7)
    assert not conteudo.progresso_visivel()
    janela.remove(conteudo.raiz)
    janela.destroy()


def test_voltar_o_mouse_a_tempo_cancela_o_sumico(app):
    ctx, conteudo = _com_radio_tocando(app)
    janela = _janela_1366(conteudo)
    conteudo.mostrar_o_progresso(True)
    conteudo.esconder_o_progresso_depois_de_uma_pausa()
    conteudo.mostrar_o_progresso(True)                  # o mouse voltou
    girar(0.7)
    assert conteudo.progresso_visivel()
    janela.remove(conteudo.raiz)
    janela.destroy()


def test_o_progresso_flutua_por_cima_e_nao_mexe_na_altura_da_tela(app):
    """Mostrar o progresso não redimensiona a tela de baixo (isso pesaria no notebook antigo)."""
    ctx, conteudo = _com_radio_tocando(app)
    janela = _janela_1366(conteudo)
    antes = conteudo.pilha.get_allocated_height()
    conteudo.mostrar_o_progresso(True)
    girar(0.4)
    depois = conteudo.pilha.get_allocated_height()
    janela.remove(conteudo.raiz)
    janela.destroy()
    assert antes == depois


def test_um_fio_fino_sempre_mostra_o_andamento_mesmo_sem_o_mouse(app):
    ctx, conteudo = _com_radio_tocando(app)
    assert conteudo.fio_do_radio is not None and conteudo.fio_do_radio.get_visible()
    conteudo.fio_do_radio.set_fraction(0)
    conteudo.atualizar_progresso_do_mini()
    assert 0.0 <= conteudo.fio_do_radio.get_fraction() <= 1.0


def test_a_barra_do_pe_tem_o_visor_escuro_sem_ruler_antiga(app):
    ctx, conteudo = _com_radio_tocando(app)
    from moa.ui import theme
    css = theme.gerar_css("normal", "maior")
    assert "#FFE9A8" not in css and "#F2CF76" not in css        # o âmbar terroso do visor saiu de vez
