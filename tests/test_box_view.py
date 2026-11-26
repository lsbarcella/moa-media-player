# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes da Caixa e da tela de editar disco (M4)."""

import gi
import pytest

gi.require_version("Gtk", "3.0")

from moa.core import box, custom_albums  # noqa: E402
from moa.core.session import Tela  # noqa: E402
from tests.test_ui_smoke import app, musica  # noqa: E402,F401  (fixtures)
from tests.ui_ajuda import botao_com_texto, botoes, desenhar, textos, tem_display  # noqa: E402

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


def abrir_editar(ctx, conteudo, indice=0):
    ctx.radio.abrir_disco(ctx.discos[indice], tocar=False)
    ctx.session.ir_para(Tela.RADIO)
    botao_com_texto(conteudo.telas[Tela.RADIO].raiz, "Mexer neste disco").clicked()
    assert ctx.session.tela == Tela.EDITAR
    return conteudo.telas[Tela.EDITAR]


def todo_o_texto_menos_a_caixa(ctx, conteudo):
    """Junta o texto de todas as telas, exceto a Caixa, para provar o que NÃO aparece."""
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    achados = []
    for tela in Tela:
        if tela == Tela.CAIXA or tela not in conteudo.telas:
            continue
        ctx.session.ir_para(tela)
        achados += textos(conteudo.raiz)
    return achados


# -- Caixa --------------------------------------------------------------------------------------

def test_apagar_de_vez_nunca_aparece_fora_da_caixa(app):
    ctx, conteudo = app
    box.tirar_da_estante(ctx.banco, ctx.discos[2].id)
    ctx.recarregar()
    assert not any("Apagar de vez" in t for t in todo_o_texto_menos_a_caixa(ctx, conteudo))
    ctx.session.ir_para(Tela.CAIXA)
    assert "Apagar de vez…" in textos(conteudo.telas[Tela.CAIXA].raiz)


def test_o_botao_da_caixa_na_estante_conta_os_discos(app):
    ctx, conteudo = app
    assert "A Caixa (0 discos)" in textos(conteudo.telas[Tela.ESTANTE].raiz)
    box.tirar_da_estante(ctx.banco, ctx.discos[0].id)
    ctx.recarregar()
    assert "A Caixa (1 disco)" in textos(conteudo.telas[Tela.ESTANTE].raiz)
    botao_com_texto(conteudo.telas[Tela.ESTANTE].raiz, "A Caixa (1 disco)").clicked()
    assert ctx.session.tela == Tela.CAIXA


def test_caixa_vazia_diz_que_esta_vazia(app):
    ctx, conteudo = app
    ctx.session.ir_para(Tela.CAIXA)
    assert "A Caixa está vazia." in textos(conteudo.telas[Tela.CAIXA].raiz)


def test_manter_o_disco_nao_apaga_e_sim_apaga_so_aquele_disco(app, musica):
    ctx, conteudo = app
    alvo, outro = ctx.discos[0], ctx.discos[1]
    box.tirar_da_estante(ctx.banco, alvo.id)
    ctx.recarregar()
    ctx.session.ir_para(Tela.CAIXA)
    raiz = lambda: conteudo.telas[Tela.CAIXA].raiz
    botao_com_texto(raiz(), "Apagar de vez…").clicked()
    t = textos(raiz())
    assert any("serão apagados do computador e não voltam" in x for x in t)
    botao_com_texto(raiz(), "Manter o disco").clicked()
    assert all(f.path.exists() for f in alvo.tracks) and "Sim, apagar de vez" not in textos(raiz())
    botao_com_texto(raiz(), "Apagar de vez…").clicked()
    botao_com_texto(raiz(), "Sim, apagar de vez").clicked()
    assert not any(f.path.exists() for f in alvo.tracks)
    assert all(f.path.exists() for f in outro.tracks)
    assert ctx.caixa == [] and "A Caixa está vazia." in textos(raiz())
    assert f"Apaguei “{alvo.title}” de vez." in textos(raiz())


def test_pergunta_do_disco_montado_diz_que_so_desfaz_o_disco(app):
    ctx, conteudo = app
    mix_id = custom_albums.criar(ctx.banco, "Domingo", [str(ctx.discos[0].tracks[0].path)])
    box.tirar_da_estante(ctx.banco, mix_id)
    ctx.recarregar()
    ctx.session.ir_para(Tela.CAIXA)
    botao_com_texto(conteudo.telas[Tela.CAIXA].raiz, "Apagar de vez…").clicked()
    assert any("O disco montado será desfeito" in x for x in textos(conteudo.telas[Tela.CAIXA].raiz))
    botao_com_texto(conteudo.telas[Tela.CAIXA].raiz, "Sim, apagar de vez").clicked()
    assert ctx.caixa == [] and ctx.discos[0].tracks[0].path.exists()


def test_falha_ao_apagar_mostra_frase_calma_sem_jargao(app, monkeypatch):
    ctx, conteudo = app
    box.tirar_da_estante(ctx.banco, ctx.discos[0].id)
    ctx.recarregar()
    ctx.session.ir_para(Tela.CAIXA)

    def quebrar(*_a, **_k):
        raise PermissionError("[Errno 13] Permission denied")

    monkeypatch.setattr(box, "apagar_de_vez", quebrar)
    botao_com_texto(conteudo.telas[Tela.CAIXA].raiz, "Apagar de vez…").clicked()
    botao_com_texto(conteudo.telas[Tela.CAIXA].raiz, "Sim, apagar de vez").clicked()
    t = textos(conteudo.telas[Tela.CAIXA].raiz)
    assert "Não consegui apagar tudo. O que sobrou continua na Caixa." in t
    assert not any("Errno" in x or "Permission" in x for x in t)
    assert len(ctx.caixa) == 1


def test_colocar_de_volta_na_estante(app):
    ctx, conteudo = app
    alvo = ctx.discos[0]
    box.tirar_da_estante(ctx.banco, alvo.id)
    ctx.recarregar()
    ctx.session.ir_para(Tela.CAIXA)
    botao_com_texto(conteudo.telas[Tela.CAIXA].raiz, "Colocar de volta na estante").clicked()
    assert alvo.id in {d.id for d in ctx.discos} and ctx.caixa == []


# -- editar ------------------------------------------------------------------------------------------

def test_o_nome_atualiza_a_previa_a_cada_letra(app):
    ctx, conteudo = app
    visao = abrir_editar(ctx, conteudo)
    visao.campo_do_nome.set_text("Os Boleros")
    assert "Os Boleros" in textos(visao._area_da_previa)
    visao.campo_do_nome.set_text("")
    assert "(sem nome)" in textos(visao._area_da_previa)


def test_deixar_como_estava_nao_grava_nada_e_volta(app):
    ctx, conteudo = app
    visao = abrir_editar(ctx, conteudo)
    visao.campo_do_nome.set_text("Mudei")
    botao_com_texto(visao.raiz, "Deixar como estava").clicked()
    assert ctx.session.tela == Tela.RADIO
    assert ctx.banco.load_overrides() == {}


def test_guardar_muda_o_nome_e_como_era_antes_restaura(app):
    ctx, conteudo = app
    original = ctx.discos[0].title
    visao = abrir_editar(ctx, conteudo)
    visao.campo_do_nome.set_text("Os Boleros do Pai")
    botao_com_texto(visao.raiz, "Guardar").clicked()
    assert ctx.session.tela == Tela.RADIO
    assert ctx.radio.disco.title == "Os Boleros do Pai"              # o rádio já mostra o nome novo
    t = textos(conteudo.telas[Tela.RADIO].raiz)
    assert "Guardei. O disco agora se chama “Os Boleros do Pai”." in t and "Como era antes" in t
    botao_com_texto(conteudo.telas[Tela.RADIO].raiz, "Como era antes").clicked()
    assert ctx.radio.disco.title == original and original in [d.title for d in ctx.discos]


def test_nome_vazio_mantem_o_nome_atual(app):
    ctx, conteudo = app
    original = ctx.discos[0].title
    visao = abrir_editar(ctx, conteudo)
    visao.campo_do_nome.set_text("   ")
    botao_com_texto(visao.raiz, "Guardar").clicked()
    assert original in [d.title for d in ctx.discos]


def test_galeria_de_capas_e_troca_para_a_desenhada(app):
    ctx, conteudo = app
    visao = abrir_editar(ctx, conteudo)
    t = textos(visao.raiz)
    assert "Capa desenhada" in t and "Trocar a capa" in t
    botao_com_texto(visao.raiz, "Capa desenhada").clicked()
    assert any("Escolhida" in x for x in textos(visao.raiz))
    botao_com_texto(visao.raiz, "Guardar").clicked()
    assert ctx.banco.load_overrides()[ctx.radio.disco.id].cover_kind == "drawn"


def test_editar_disco_montado_so_mostra_o_nome(app):
    ctx, conteudo = app
    mix_id = custom_albums.criar(ctx.banco, "Domingo", [str(ctx.discos[0].tracks[0].path)])
    ctx.recarregar()
    ctx.radio.abrir_disco(ctx.montados[0], tocar=False)
    ctx.session.ir_para(Tela.RADIO)
    botao_com_texto(conteudo.telas[Tela.RADIO].raiz, "Mexer neste disco").clicked()
    t = textos(conteudo.telas[Tela.EDITAR].raiz)
    assert "Trocar a capa" not in t and any("feita com as capas" in x for x in t)


def test_tirar_da_estante_pela_tela_de_editar_leva_para_a_caixa_com_desfazer(app):
    ctx, conteudo = app
    alvo = ctx.discos[0]
    visao = abrir_editar(ctx, conteudo)
    botao_com_texto(visao.raiz, "Tirar da estante").clicked()
    assert ctx.session.tela == Tela.ESTANTE and not ctx.radio.tem_disco
    assert [d.id for d in ctx.caixa] == [alvo.id] and alvo.id not in {d.id for d in ctx.discos}
    t = textos(conteudo.telas[Tela.ESTANTE].raiz)
    assert any("as músicas continuam no computador" in x for x in t)
    assert all(f.path.exists() for f in alvo.tracks)
    botao_com_texto(conteudo.telas[Tela.ESTANTE].raiz, "Desfazer").clicked()
    assert ctx.caixa == [] and alvo.id in {d.id for d in ctx.discos}


def test_as_telas_da_caixa_e_de_editar_desenham_sem_erro(app, tmp_path):
    ctx, conteudo = app
    visao = abrir_editar(ctx, conteudo)
    assert desenhar(conteudo, tmp_path / "editar.png").get_width() == 1100
    box.tirar_da_estante(ctx.banco, ctx.discos[1].id)
    ctx.recarregar()
    ctx.session.ir_para(Tela.CAIXA)
    assert desenhar(conteudo, tmp_path / "caixa.png").get_width() == 1100
