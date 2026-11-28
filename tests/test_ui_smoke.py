# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes de interface (M3): estante e rádio, desenhados fora da tela (KTD15)."""

import pytest

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from moa.core.config import Preferencias  # noqa: E402
from moa.core.contexto import Contexto  # noqa: E402
from moa.core.db import Database  # noqa: E402
from moa.core.library import scan  # noqa: E402
from moa.core.session import Tela  # noqa: E402
from moa.ui import theme  # noqa: E402
from moa.ui.window import Conteudo  # noqa: E402
from tests.test_player import _sink_no_relogio, _sink_rapido  # noqa: E402
from tests.ui_ajuda import botao_com_texto, botoes, desenhar, girar, textos, tem_display  # noqa: E402

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


@pytest.fixture
def musica(make_track, tmp_path):
    raiz = tmp_path / "musica"
    for artista, album in (("Zeca", "Samba"), ("Ana", "Boleros"), ("Ana", "Antigos")):
        for n in (1, 2, 3):
            make_track(raiz / f"{artista} {album}", f"{n:02d}.mp3", title=f"{album} {n}",
                       album=album, artist=artista, albumartist=artista, tracknumber=str(n))
    return raiz


def montar(tmp_path, musica, sink=_sink_rapido, carregado=True):
    banco = Database(tmp_path / "moa.db")
    prefs = Preferencias(tmp_path / "config.json")
    theme.aplicar(prefs.config.paleta, prefs.config.letra)
    ctx = Contexto(banco, prefs, musica, sink_factory=sink, pasta_miniaturas=tmp_path / "miniaturas")
    conteudo = Conteudo(ctx)
    if carregado:
        ctx.definir_colecao(scan(musica), {})
    return ctx, conteudo


@pytest.fixture
def app(tmp_path, musica):
    ctx, conteudo = montar(tmp_path, musica)
    yield ctx, conteudo
    ctx.encerrar()
    ctx.banco.close()


def titulos_dos_discos(conteudo):
    return [t for t in textos(conteudo.telas[Tela.ESTANTE].raiz)
            if t in {"Samba", "Boleros", "Antigos"}]


# -- Estante ------------------------------------------------------------------------------

def test_estante_ordena_por_artista_e_depois_album(app):
    ctx, conteudo = app
    assert titulos_dos_discos(conteudo) == ["Antigos", "Boleros", "Samba"]


def test_a_estante_desenha_sem_erro_e_gera_imagem(app, tmp_path):
    _, conteudo = app
    pixbuf = desenhar(conteudo, tmp_path / "estante.png")
    assert pixbuf.get_width() == 1100 and (tmp_path / "estante.png").stat().st_size > 2000


def test_estante_sem_botao_de_voltar(app):
    _, conteudo = app
    assert "Voltar para a estante" not in textos(conteudo.cabecalho)
    assert "Minha estante" in textos(conteudo.cabecalho)


def test_um_clique_na_capa_poe_o_disco_no_radio_e_toca(app):
    ctx, conteudo = app
    botao_com_texto(conteudo.telas[Tela.ESTANTE].raiz, "Boleros").clicked()
    girar(0.2)
    assert ctx.session.tela == Tela.RADIO
    assert ctx.radio.disco.title == "Boleros"


def test_primeira_abertura_mostra_carregando_e_nao_a_frase_de_vazio(tmp_path, musica):
    ctx, conteudo = montar(tmp_path, musica, carregado=False)
    try:
        t = textos(conteudo.telas[Tela.ESTANTE].raiz)
        assert "Estou procurando os seus discos..." in t
        assert not any("Ainda não há discos" in x for x in t)
    finally:
        ctx.encerrar(); ctx.banco.close()


def test_colecao_vazia_mostra_frase_calma_depois_da_varredura(tmp_path):
    vazia = tmp_path / "vazia"
    vazia.mkdir()
    ctx, conteudo = montar(tmp_path, vazia)
    try:
        t = textos(conteudo.telas[Tela.ESTANTE].raiz)
        assert any("Ainda não há discos" in x for x in t)
        assert "Estou procurando os seus discos..." not in t
    finally:
        ctx.encerrar(); ctx.banco.close()


def test_continuar_a_ouvir_aparece_com_posicao_guardada_e_clicar_toca(app):
    ctx, conteudo = app
    disco = ctx.disco(ctx.discos[1].id)
    ctx.memoria.guardar_onde_parou(disco.id, 2, 0.0)
    conteudo.redesenhar()
    t = textos(conteudo.telas[Tela.ESTANTE].raiz)
    assert f"Você parou em {disco.title}, faixa 3." in t
    botao_com_texto(conteudo.telas[Tela.ESTANTE].raiz, "Continuar a ouvir").clicked()
    girar(0.2)
    assert ctx.radio.disco.id == disco.id and ctx.player.indice >= 2 or ctx.radio.tem_disco


def test_disco_no_radio_vira_lugar_vazio_na_estante(app):
    ctx, conteudo = app
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    ctx.session.ir_para(Tela.ESTANTE)
    t = textos(conteudo.telas[Tela.ESTANTE].raiz)
    assert "Em uso no rádio" in t and "Ir ao rádio" in t
    assert not any("Você parou em" in x for x in t)       # com disco no rádio, não há "continuar"


def test_ouvidos_ha_pouco_mostra_os_recentes(app):
    ctx, conteudo = app
    ctx.memoria.registrar_recente(ctx.discos[2].id)
    conteudo.redesenhar()
    assert "Ouvidos há pouco" in textos(conteudo.telas[Tela.ESTANTE].raiz)


# -- Rádio ----------------------------------------------------------------------------------

@pytest.fixture
def disco_longo(faixa_longa):
    """Um disco de 3 faixas de ~4,6 s: dá tempo de olhar o rádio ainda tocando."""
    from moa.core.models import Album, Track
    faixas = tuple(Track(path=faixa_longa, title=f"Longa {n}", number=n) for n in (1, 2, 3))
    return Album(folder=faixa_longa.parent, title="Longos", artist="Teste", tracks=faixas)


def abrir_radio(ctx, indice=0, tocar=True, espera=0.0):
    """Põe o primeiro disco no rádio. As faixas de teste duram ~93 ms: quem precisa
    ver o rádio ainda tocando não deve esperar (`espera=0`)."""
    ctx.radio.abrir_disco(ctx.discos[0], indice=indice, tocar=tocar)
    ctx.session.ir_para(Tela.RADIO)
    girar(espera)


def test_visor_e_botao_principal_acompanham_o_estado(tmp_path, musica, disco_longo):
    ctx, conteudo = montar(tmp_path, musica, sink=_sink_no_relogio)
    try:
        ctx.radio.abrir_disco(disco_longo, indice=1, tocar=True)
        ctx.session.ir_para(Tela.RADIO)
        raiz = conteudo.telas[Tela.RADIO].raiz
        assert "TOCANDO: Faixa 2 de 3" in textos(raiz) and "Pausar" in textos(raiz)
        botao_com_texto(raiz, "Pausar").clicked()
        girar(0.1)
        raiz = conteudo.telas[Tela.RADIO].raiz
        assert "PAUSADO. Aperte Tocar para continuar" in textos(raiz) and "Tocar" in textos(raiz)
    finally:
        ctx.encerrar(); ctx.banco.close()


def test_volume_no_maximo_o_botao_vira_no_maximo_e_clicar_avisa(app):
    ctx, conteudo = app
    abrir_radio(ctx, tocar=False)
    ctx.player.definir_degrau_de_volume(10)
    conteudo.redesenhar()
    raiz = conteudo.telas[Tela.RADIO].raiz
    assert "Volume: 10 de 10" in textos(raiz)           # o estado continua escrito
    botao_com_texto(raiz, "Volume no máximo").clicked()   # a tecla só tem o símbolo; o nome é acessível
    assert "O volume já está no máximo." in textos(conteudo.telas[Tela.RADIO].raiz)
    assert ctx.player.degrau_de_volume == 10


def test_voz_mais_clara_mostra_o_estado_em_texto(app):
    ctx, conteudo = app
    abrir_radio(ctx, tocar=False)
    assert "Voz mais clara: desligada" in textos(conteudo.telas[Tela.RADIO].raiz)
    botao_com_texto(conteudo.telas[Tela.RADIO].raiz, "Voz mais clara: desligada").clicked()
    assert "Voz mais clara: ligada" in textos(conteudo.telas[Tela.RADIO].raiz)


def test_aviso_do_visor_fica_ate_a_proxima_acao(app):
    ctx, conteudo = app
    abrir_radio(ctx, tocar=False)
    botao_com_texto(conteudo.telas[Tela.RADIO].raiz, "Mais alto").clicked()
    girar(0.8)                                            # o tempo passa
    assert "Volume mais alto (7 de 10)" in textos(conteudo.telas[Tela.RADIO].raiz)
    botao_com_texto(conteudo.telas[Tela.RADIO].raiz, "Mais baixo").clicked()
    assert "Volume mais alto (7 de 10)" not in textos(conteudo.telas[Tela.RADIO].raiz)


def test_aviso_da_sessao_fica_na_tela_e_some_na_proxima_acao(app):
    ctx, conteudo = app
    ctx.session.mostrar_aviso("Guardei o disco na estante.")
    girar(0.6)
    assert "Guardei o disco na estante." in textos(conteudo.telas[Tela.ESTANTE].raiz)
    ctx.session.acao()
    assert "Guardei o disco na estante." not in textos(conteudo.telas[Tela.ESTANTE].raiz)


def tecla(valor):
    evento = Gdk.Event.new(Gdk.EventType.KEY_PRESS)
    evento.keyval = valor
    evento.state = 0
    return evento


def test_proxima_e_depois_espaco_pausa_e_nao_avanca_de_novo(tmp_path, musica, disco_longo):
    ctx, conteudo = montar(tmp_path, musica, sink=_sink_no_relogio)
    try:
        ctx.radio.abrir_disco(disco_longo, tocar=True)
        ctx.session.ir_para(Tela.RADIO)
        botao_com_texto(conteudo.telas[Tela.RADIO].raiz, "Próxima").clicked()
        girar(0.1)
        assert ctx.player.indice == 1
        assert conteudo.tratar_tecla(tecla(Gdk.KEY_space), None) is True
        girar(0.1)
        assert ctx.player.indice == 1 and not ctx.radio.tocando
    finally:
        ctx.encerrar(); ctx.banco.close()


def test_atalhos_de_teclado_e_campo_de_texto_tem_prioridade(app):
    ctx, conteudo = app
    abrir_radio(ctx, tocar=False)
    assert conteudo.tratar_tecla(tecla(Gdk.KEY_Up), None) is True
    assert ctx.player.degrau_de_volume == 7
    assert conteudo.tratar_tecla(tecla(Gdk.KEY_Down), None) is True
    assert ctx.player.degrau_de_volume == 6
    campo = Gtk.Entry()
    assert conteudo.tratar_tecla(tecla(Gdk.KEY_space), campo) is False     # digitando
    assert conteudo.tratar_tecla(tecla(Gdk.KEY_a), None) is False


def test_sem_disco_no_radio_as_teclas_nao_fazem_nada(app):
    _, conteudo = app
    assert conteudo.tratar_tecla(tecla(Gdk.KEY_space), None) is False


def test_alvos_de_64px_na_escala_normal(app):
    ctx, conteudo = app
    abrir_radio(ctx, tocar=False)
    desenhar(conteudo)
    # Os botões não podem ser mais baixos que 64 px (a janela foi desenhada fora da tela).
    pequenos = []
    for tela in (Tela.RADIO,):
        raiz = conteudo.telas[tela].raiz
        janela = Gtk.OffscreenWindow()
        janela.set_size_request(1100, 760)
        janela.add(conteudo.raiz)
        janela.show_all()
        girar(0.3)
        for b in botoes(raiz):
            if b.get_mapped() and b.get_allocated_height() < 64:
                pequenos.append((textos(b), b.get_allocated_height()))
        janela.remove(conteudo.raiz)
        janela.destroy()
    assert not pequenos, pequenos


def test_mini_radio_aparece_fora_do_radio_quando_ha_musica(app):
    ctx, conteudo = app
    abrir_radio(ctx, tocar=True)
    assert conteudo.mini.get_visible() is False
    ctx.session.ir_para(Tela.ESTANTE)
    assert conteudo.mini.get_visible() is True
    assert "Abrir o rádio" in textos(conteudo.mini)
    botao_com_texto(conteudo.mini, "Abrir o rádio").clicked()
    assert ctx.session.tela == Tela.RADIO


def test_voltar_para_a_estante_aparece_no_radio_e_funciona(app):
    ctx, conteudo = app
    abrir_radio(ctx, tocar=False)
    botao_com_texto(conteudo.cabecalho, "Voltar para a estante").clicked()
    assert ctx.session.tela == Tela.ESTANTE


def test_falha_inesperada_mostra_frase_calma_em_qualquer_tela(app):
    ctx, conteudo = app
    from moa.core.logsetup import MSG_FALHA_INESPERADA
    for tela in (Tela.ESTANTE, Tela.CAIXA, Tela.CONFIGURACOES):
        ctx.session.ir_para(tela)
        ctx.session.mostrar_falha(MSG_FALHA_INESPERADA)
        girar(0.3)
        assert MSG_FALHA_INESPERADA in textos(conteudo.raiz)
        ctx.session.acao()
        assert MSG_FALHA_INESPERADA not in textos(conteudo.raiz)


def test_fechar_grava_onde_parou_e_reabrir_mostra_continuar_a_ouvir(tmp_path, musica):
    ctx, conteudo = montar(tmp_path, musica)
    disco = ctx.discos[0]
    ctx.radio.abrir_disco(disco, indice=1, tocar=False)
    ctx.encerrar()                    # o que o X da janela faz
    ctx.banco.close()
    # "reabre o app": novo contexto sobre o mesmo banco
    ctx2, conteudo2 = montar(tmp_path, musica)
    try:
        t = textos(conteudo2.telas[Tela.ESTANTE].raiz)
        assert f"Você parou em {disco.title}, faixa 2." in t
        assert "Continuar a ouvir" in t
    finally:
        ctx2.encerrar(); ctx2.banco.close()
