# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes da tela "Criar uma playlist" e do painel do "+" (M4)."""

import re
import sqlite3

import gi
import pytest

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from moa.core import custom_albums  # noqa: E402
from moa.core.session import Tela  # noqa: E402
from tests.test_ui_smoke import app, montar, musica, tecla  # noqa: E402,F401  (fixtures e ajudas)
from tests.ui_ajuda import (botao_com_texto, botoes, desenhar, girar, textos,  # noqa: E402
                            tem_display, todos_os_widgets)

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


def abrir_playlist(ctx, conteudo):
    botao_com_texto(conteudo.telas[Tela.ESTANTE].raiz, "Criar uma playlist").clicked()
    assert ctx.session.tela == Tela.PLAYLIST
    return conteudo.telas[Tela.PLAYLIST]


def marcar(visao, titulo):
    botao_com_texto(visao.raiz, titulo).clicked()


# -- tela de criar playlist --------------------------------------------------------------------

def test_comeca_sem_musicas_e_o_botao_de_guardar_esta_inativo(app):
    ctx, conteudo = app
    visao = abrir_playlist(ctx, conteudo)
    t = textos(visao.raiz)
    assert "Nenhuma música escolhida" in t and "Marque pelo menos uma música" in t
    assert "Guardar na estante" not in t


def test_digitar_com_o_foco_fora_do_campo_vai_para_a_busca_e_filtra(app):
    ctx, conteudo = app
    visao = abrir_playlist(ctx, conteudo)
    assert conteudo.tratar_tecla(tecla(Gdk.KEY_b), None) is True
    assert visao.campo_de_busca.get_text() == "b"
    assert conteudo.tratar_tecla(tecla(Gdk.KEY_space), None) is True       # espaço também é letra aqui
    assert visao.campo_de_busca.get_text() == "b "
    visao.campo_de_busca.set_text("Boleros 2")
    nomes = [t for t in textos(visao._area_da_lista) if t.startswith(("Boleros", "Samba", "Antigos"))]
    assert "Boleros 2" in nomes and "Samba 1" not in nomes


def test_marcar_3_filtrar_e_limpar_mantem_as_3_marcadas(app):
    ctx, conteudo = app
    visao = abrir_playlist(ctx, conteudo)
    for titulo in ("Boleros 1", "Samba 2", "Antigos 3"):
        marcar(visao, titulo)
    visao.campo_de_busca.set_text("Samba")
    assert "3 músicas escolhidas" in textos(visao.raiz)
    visao.campo_de_busca.set_text("")
    assert "3 músicas escolhidas" in textos(visao.raiz)
    assert textos(visao._area_do_cartao).count("Marcada") == 0
    assert sum(1 for t in textos(visao._area_da_lista) if t == "Marcada") == 3


def test_guardar_cria_o_disco_volta_a_estante_e_o_aviso_fica_ate_a_proxima_acao(app):
    ctx, conteudo = app
    visao = abrir_playlist(ctx, conteudo)
    marcar(visao, "Samba 1")
    marcar(visao, "Boleros 2")
    botao_com_texto(visao.raiz, "Guardar na estante").clicked()
    assert ctx.session.tela == Tela.ESTANTE
    [montado] = ctx.montados
    assert [t.title for t in montado.tracks] == ["Samba 1", "Boleros 2"]       # ordem de marcar
    assert re.fullmatch(r"Meu disco de \d\d/\d\d", montado.title)
    esperado = f"Pronto! O disco “{montado.title}” está na estante."
    girar(0.6)
    assert esperado in textos(conteudo.telas[Tela.ESTANTE].raiz)
    assert "Discos que montei" in textos(conteudo.telas[Tela.ESTANTE].raiz)
    ctx.session.acao()
    assert esperado not in textos(conteudo.telas[Tela.ESTANTE].raiz)


def test_mudar_o_nome_e_guardar(app):
    ctx, conteudo = app
    visao = abrir_playlist(ctx, conteudo)
    marcar(visao, "Samba 1")
    botao_com_texto(visao.raiz, "Mudar o nome").clicked()
    visao.campo_do_nome.set_text("Domingo")
    botao_com_texto(visao.raiz, "Pronto, este nome").clicked()
    assert "Domingo" in textos(visao.raiz)
    botao_com_texto(visao.raiz, "Guardar na estante").clicked()
    assert [m.title for m in ctx.montados] == ["Domingo"]


def test_falha_ao_guardar_mostra_frase_calma_e_mantem_as_marcacoes(app, monkeypatch):
    ctx, conteudo = app
    visao = abrir_playlist(ctx, conteudo)
    marcar(visao, "Samba 1")

    def quebrar(*_a, **_k):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(custom_albums, "criar", quebrar)
    botao_com_texto(visao.raiz, "Guardar na estante").clicked()
    assert ctx.session.tela == Tela.PLAYLIST
    t = textos(conteudo.telas[Tela.PLAYLIST].raiz)
    assert any("Não consegui guardar o disco" in x for x in t)
    assert not any("database" in x or "locked" in x for x in t)          # nada técnico para o idoso
    assert "1 música escolhida" in t and ctx.montados == []


def test_voltar_para_a_estante_a_partir_da_playlist(app):
    ctx, conteudo = app
    abrir_playlist(ctx, conteudo)
    botao_com_texto(conteudo.cabecalho, "Voltar para a estante").clicked()
    assert ctx.session.tela == Tela.ESTANTE


def test_caixas_de_marcar_e_filtros_tem_no_minimo_64px(app):
    ctx, conteudo = app
    visao = abrir_playlist(ctx, conteudo)
    marcar(visao, "Samba 1")
    janela = Gtk.OffscreenWindow()
    janela.set_size_request(1100, 760)
    janela.add(conteudo.raiz)
    janela.show_all()
    girar(0.4)
    try:
        pequenos = [(textos(b), b.get_allocated_height()) for b in botoes(visao.raiz)
                    if b.get_mapped() and b.get_allocated_height() < 64]
    finally:
        janela.remove(conteudo.raiz)
        janela.destroy()
    assert not pequenos, pequenos


def test_as_marcacoes_sobrevivem_a_ida_as_configuracoes(app):
    ctx, conteudo = app
    visao = abrir_playlist(ctx, conteudo)
    marcar(visao, "Samba 1")
    botao_com_texto(conteudo.cabecalho, "Configurações").clicked()
    botao_com_texto(conteudo.cabecalho, "Voltar para onde eu estava").clicked()
    assert ctx.session.tela == Tela.PLAYLIST
    assert "1 música escolhida" in textos(conteudo.telas[Tela.PLAYLIST].raiz)


def test_a_playlist_desenha_sem_erro(app, tmp_path):
    ctx, conteudo = app
    visao = abrir_playlist(ctx, conteudo)
    marcar(visao, "Samba 1")
    marcar(visao, "Boleros 1")
    assert desenhar(conteudo, tmp_path / "playlist.png").get_width() == 1100


# -- botão "+" -------------------------------------------------------------------------------------

def abrir_radio_e_mais(ctx, conteudo, indice=0):
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    ctx.session.ir_para(Tela.RADIO)
    botoes_mais = [b for b in botoes(conteudo.telas[Tela.RADIO].raiz)
                   if "Colocar em outro disco" in textos(b)]
    botoes_mais[indice].clicked()


def painel_aberto(conteudo):
    return conteudo.plus.raiz.get_visible() and "Em qual disco?" in textos(conteudo.plus.raiz)


def test_o_mais_abre_o_painel_com_disco_novo_primeiro_e_cancelar_fecha(app):
    ctx, conteudo = app
    custom_albums.criar(ctx.banco, "Domingo", [str(ctx.discos[1].tracks[0].path)])
    ctx.recarregar()
    abrir_radio_e_mais(ctx, conteudo)
    assert painel_aberto(conteudo)
    ordem = [t for t in textos(conteudo.plus.raiz) if t in ("Disco novo", "Domingo")]
    assert ordem == ["Disco novo", "Domingo"]
    botao_com_texto(conteudo.plus.raiz, "Cancelar").clicked()
    assert not painel_aberto(conteudo)


def test_disco_novo_pelo_mais_cria_com_a_musica_nome_sem_repetir_e_desfazer_remove(app):
    ctx, conteudo = app
    abrir_radio_e_mais(ctx, conteudo, indice=1)
    botao_com_texto(conteudo.plus.raiz, "Disco novo").clicked()
    [montado] = ctx.montados
    assert [t.title for t in montado.tracks] == [ctx.radio.disco.tracks[1].title]
    assert re.fullmatch(r"Meu disco de \d\d/\d\d", montado.title)
    linha = textos(conteudo.telas[Tela.RADIO].raiz)
    assert f"Criei o disco “{montado.title}” com esta música." in linha
    botao_com_texto(conteudo.telas[Tela.RADIO].raiz, "Desfazer").clicked()
    assert ctx.montados == []
    # Um segundo "disco novo" depois de desfazer volta a usar o nome simples.
    abrir_radio_e_mais(ctx, conteudo)
    botao_com_texto(conteudo.plus.raiz, "Disco novo").clicked()
    abrir_radio_e_mais(ctx, conteudo, indice=2)
    botao_com_texto(conteudo.plus.raiz, "Disco novo").clicked()
    nomes = sorted(m.title for m in ctx.montados)
    assert len(nomes) == 2 and nomes[0] != nomes[1] and nomes[1].endswith("(2)")


def test_colocar_em_disco_existente_confirma_na_linha_e_nao_duplica(app):
    ctx, conteudo = app
    custom_albums.criar(ctx.banco, "Domingo", [str(ctx.discos[1].tracks[0].path)])
    ctx.recarregar()
    abrir_radio_e_mais(ctx, conteudo)
    botao_com_texto(conteudo.plus.raiz, "Domingo").clicked()
    assert "Está no disco “Domingo”." in textos(conteudo.telas[Tela.RADIO].raiz)
    assert len(ctx.montados[0].tracks) == 2
    ctx.session.acao()
    abrir_radio_e_mais(ctx, conteudo)
    botao_com_texto(conteudo.plus.raiz, "Domingo").clicked()
    assert "Esta música já está no disco “Domingo”." in textos(conteudo.telas[Tela.RADIO].raiz)
    assert len(ctx.montados[0].tracks) == 2


def test_desfazer_do_mais_remove_a_musica_e_outra_acao_faz_o_aviso_sumir(app):
    ctx, conteudo = app
    custom_albums.criar(ctx.banco, "Domingo", [str(ctx.discos[1].tracks[0].path)])
    ctx.recarregar()
    abrir_radio_e_mais(ctx, conteudo)
    botao_com_texto(conteudo.plus.raiz, "Domingo").clicked()
    botao_com_texto(conteudo.telas[Tela.RADIO].raiz, "Desfazer").clicked()
    assert len(ctx.montados[0].tracks) == 1
    # Agora de novo, mas clicando em outra coisa antes: aviso e "Desfazer" somem.
    abrir_radio_e_mais(ctx, conteudo)
    botao_com_texto(conteudo.plus.raiz, "Domingo").clicked()
    botao_com_texto(conteudo.telas[Tela.RADIO].raiz, "Mais alto").clicked()
    t = textos(conteudo.telas[Tela.RADIO].raiz)
    assert "Está no disco “Domingo”." not in t and "Desfazer" not in t
