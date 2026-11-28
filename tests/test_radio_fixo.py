# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""O painel do rádio fica parado e só a lista de músicas rola ao lado (ADR-0028)."""

import gi
import pytest

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.session import Tela  # noqa: E402
from tests.test_ui_smoke import montar  # noqa: E402
from tests.ui_ajuda import botao_com_texto, girar, tem_display  # noqa: E402

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


@pytest.fixture
def disco_longo(make_track, tmp_path):
    raiz = tmp_path / "musica"
    for n in range(1, 41):
        make_track(raiz / "Longo", f"{n:02d}.mp3", title=f"Faixa longa {n}", album="Longo",
                   artist="Ana", albumartist="Ana", tracknumber=str(n))
    ctx, conteudo = montar(tmp_path, raiz)
    yield ctx, conteudo
    ctx.encerrar()
    ctx.banco.close()


def _abrir(ctx, conteudo, letra="normal", largura=1366, altura=768):
    ctx.preferencias.mudar(letra=letra)
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    ctx.session.ir_para(Tela.RADIO)
    janela = Gtk.OffscreenWindow()
    janela.set_size_request(largura, altura)
    janela.add(conteudo.raiz)
    janela.show_all()
    girar(0.8)
    return janela


def _fechar(conteudo, janela):
    janela.remove(conteudo.raiz)
    janela.destroy()


def test_rolar_a_lista_nao_move_o_painel_do_radio(disco_longo):
    ctx, conteudo = disco_longo
    janela = _abrir(ctx, conteudo)
    radio = conteudo.telas[Tela.RADIO]
    assert radio._empilhado is False
    tocar = botao_com_texto(radio.raiz, "Tocar")
    antes = tocar.translate_coordinates(janela, 0, 0)[1]
    ajuste = radio.lista_rolagem.get_vadjustment()
    assert ajuste.get_upper() > ajuste.get_page_size()          # a lista de verdade é maior que a tela
    ajuste.set_value(ajuste.get_upper())
    girar(0.4)
    depois = tocar.translate_coordinates(janela, 0, 0)[1]
    rolou = ajuste.get_value()
    _fechar(conteudo, janela)
    assert rolou > 0
    assert antes == depois                                       # o painel e os botões ficaram onde estavam


def test_a_tela_do_radio_nao_rola_inteira_quando_as_colunas_estao_lado_a_lado(disco_longo):
    ctx, conteudo = disco_longo
    janela = _abrir(ctx, conteudo)
    radio = conteudo.telas[Tela.RADIO]
    externa = radio.rolagem_externa
    politica_v = externa.get_policy()[1]
    _fechar(conteudo, janela)
    assert politica_v == Gtk.PolicyType.NEVER


def test_empilhado_a_tela_volta_a_rolar_inteira_e_as_colunas_nao_rolam_sozinhas(disco_longo):
    ctx, conteudo = disco_longo
    janela = _abrir(ctx, conteudo, letra="maior")
    radio = conteudo.telas[Tela.RADIO]
    assert radio._empilhado is True
    assert radio.rolagem_externa.get_policy()[1] == Gtk.PolicyType.AUTOMATIC
    assert radio.painel_rolagem.get_policy()[1] == Gtk.PolicyType.NEVER
    assert radio.lista_rolagem.get_policy()[1] == Gtk.PolicyType.NEVER
    _fechar(conteudo, janela)


@pytest.mark.parametrize("letra,empilhado", [("normal", False), ("grande", False), ("maior", True)])
def test_so_a_letra_maior_empilha_as_colunas_numa_tela_larga(disco_longo, letra, empilhado):
    ctx, conteudo = disco_longo
    janela = _abrir(ctx, conteudo, letra=letra)
    assert conteudo.telas[Tela.RADIO]._empilhado is empilhado
    _fechar(conteudo, janela)


def test_numa_tela_estreita_empilha_mesmo_na_letra_normal(disco_longo):
    ctx, conteudo = disco_longo
    janela = _abrir(ctx, conteudo, largura=800)
    assert conteudo.telas[Tela.RADIO]._empilhado is True
    _fechar(conteudo, janela)


def test_a_lista_nunca_troca_de_pai_ao_mudar_de_modo(disco_longo):
    """Mudar a lista de pai refaz as centenas de linhas por dentro (era a travada): ela fica no mesmo lugar."""
    ctx, conteudo = disco_longo
    janela = _abrir(ctx, conteudo)
    radio = conteudo.telas[Tela.RADIO]
    pai_antes = radio.lugar_da_lista.get_parent()
    ctx.preferencias.mudar(letra="maior")
    conteudo.redesenhar()
    girar(0.6)
    assert radio.lugar_da_lista.get_parent() is pai_antes
    assert radio._lista.get_parent() is radio.lugar_da_lista
    _fechar(conteudo, janela)
