# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""A lista de músicas do rádio não pode ser refeita a cada clique de volume.

Num disco com centenas de músicas (a coleção do usuário tem uma pasta com 371),
refazer a lista a cada clique travava a tela. Aqui se confere QUANDO ela é refeita.
"""

import pytest

from moa.core.session import Tela
from moa.ui import widgets
from tests.test_ui_smoke import app, musica, montar  # noqa: F401  (fixtures)
from tests.ui_ajuda import girar, tem_display, textos

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


def _abrir_no_radio(ctx):
    ctx.radio.abrir_disco(ctx.discos[0])
    ctx.session.ir_para(Tela.RADIO)


def test_volume_nao_refaz_a_lista(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    ctx.radio.volume_mais()
    ctx.radio.volume_menos()
    ctx.radio.alternar_voz_mais_clara()
    assert visao._lista is antes
    assert antes.get_parent() is not None        # e continua dentro da tela


def _linha_com_a_marca(visao):
    """Índices das músicas cuja linha mostra "Tocando agora" ou "Parado aqui"."""
    return [i for i, (_moldura, nomes) in enumerate(visao._linhas)
            if {"Tocando agora", "Parado aqui"} & set(textos(nomes))]


def test_trocar_de_faixa_move_a_marca_sem_refazer_a_lista(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    assert _linha_com_a_marca(visao) == [0]
    ctx.radio.proxima()
    assert visao._lista is antes
    assert _linha_com_a_marca(visao) == [1]
    ctx.radio.tocar_faixa(2)
    assert _linha_com_a_marca(visao) == [2]
    ctx.radio.anterior()
    assert _linha_com_a_marca(visao) == [1]


def test_pausar_troca_o_texto_da_marca_sem_refazer_a_lista(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    vistos = set()
    for _ in range(2):
        ctx.radio.alternar()
        esperado = "Tocando agora" if ctx.radio.tocando else "Parado aqui"
        marca = [t for t in textos(visao._lista) if t in {"Tocando agora", "Parado aqui"}]
        assert marca == [esperado]
        vistos.add(esperado)
    assert vistos == {"Tocando agora", "Parado aqui"}      # o texto mesmo mudou
    assert visao._lista is antes


def test_a_linha_atual_fica_destacada_so_nela(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    ctx.radio.proxima()
    destacadas = [i for i, (moldura, _n) in enumerate(visao._linhas)
                  if moldura.get_style_context().has_class("moa-agora")]
    assert destacadas == [1]


def test_trocar_de_disco_refaz_a_lista(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    ctx.radio.abrir_disco(ctx.discos[1])
    assert visao._lista is not antes
    assert ctx.discos[1].tracks[0].title in textos(visao._lista)


def test_mudar_a_colecao_refaz_a_lista(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    ctx.recarregar()
    conteudo.redesenhar()
    assert visao._lista is not antes


def test_aviso_refaz_a_lista(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    antes = visao._lista
    ctx.session.mostrar_aviso("Teste", ancora=str(ctx.discos[0].tracks[0].path))
    assert visao._lista is not antes
    assert "Teste" in textos(visao._lista)


def test_icone_igual_so_e_convertido_uma_vez():
    widgets._cache_de_icones.clear()
    widgets.icone("mais")
    widgets.icone("mais")
    widgets.icone("mais", "#FFFFFF", "#1E1913")
    assert len(widgets._cache_de_icones) == 2


def test_a_lista_nunca_troca_de_pai(app):
    """Mudar um widget de pai refaz por dentro todas as linhas: era a travada com 371 faixas."""
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    pai = visao._lista.get_parent()
    for acao in (ctx.radio.volume_mais, ctx.radio.proxima, ctx.radio.alternar,
                 ctx.radio.alternar_voz_mais_clara, ctx.radio.anterior):
        acao()
        assert visao._lista.get_parent() is pai


def test_volume_nao_reaplica_o_tema(app, monkeypatch):
    """Reaplicar o tema recalcula o estilo de todos os widgets; só a letra e a cor pedem isso."""
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    chamadas = []
    monkeypatch.setattr("moa.ui.window.theme.aplicar", lambda *a: chamadas.append(a))
    ctx.radio.volume_mais()
    ctx.radio.alternar_voz_mais_clara()
    assert chamadas == []


def test_mudar_a_letra_ou_a_cor_reaplica_o_tema(app, monkeypatch):
    ctx, conteudo = app
    chamadas = []
    monkeypatch.setattr("moa.ui.window.theme.aplicar", lambda *a: chamadas.append(a))
    ctx.preferencias.mudar(letra="grande")
    assert len(chamadas) == 1 and chamadas[0][1] == "grande"
    ctx.preferencias.mudar(paleta="preto-e-branco")
    assert len(chamadas) == 2


# -- o painel do rádio é atualizado no lugar, não recriado --------------------------------------

def test_o_painel_do_radio_nao_e_recriado_a_cada_clique(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    corpo, mais, clara = visao._p.corpo, visao._p.mais, visao._p.clara
    for acao in (ctx.radio.volume_mais, ctx.radio.volume_menos, ctx.radio.alternar_voz_mais_clara,
                 ctx.radio.proxima, ctx.radio.alternar):
        acao()
        assert visao._p.corpo is corpo and visao._p.mais is mais and visao._p.clara is clara


def test_volume_atualiza_barras_texto_e_botoes(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    p = visao._p
    ctx.player.definir_degrau_de_volume(3)
    ctx.radio.volume_mais()
    degrau = ctx.player.degrau_de_volume
    assert f"Volume: {degrau} de 10" in textos(p.corpo)
    acesas = [b.get_style_context().has_class("moa-acesa") for b in p.barras]
    assert acesas == [k < degrau for k in range(10)]
    ctx.player.definir_degrau_de_volume(10)
    ctx.radio.volume_menos(); ctx.radio.volume_mais()
    assert "No máximo" in textos(p.mais) and p.mais.get_style_context().has_class("moa-inativo")
    ctx.player.definir_degrau_de_volume(0)
    ctx.radio.volume_menos()
    assert "No mínimo" in textos(p.menos)


def test_voz_mais_clara_muda_o_texto_e_a_cor(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    p = conteudo.telas[Tela.RADIO]._p
    assert "Voz mais clara: desligada" in textos(p.clara)
    ctx.radio.alternar_voz_mais_clara()
    assert "Voz mais clara: ligada" in textos(p.clara)
    assert p.clara.get_style_context().has_class("moa-clara-ligada")
    assert not p.clara.get_style_context().has_class("moa-clara-desligada")


def test_tocar_e_pausar_trocam_o_botao_do_meio_e_a_lampada(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    nomes = set()
    for _ in range(2):
        ctx.radio.alternar()
        principal = visao.botao_principal
        nomes.add(textos(principal)[0])
        assert textos(principal)[0] == ("Pausar" if ctx.radio.tocando else "Tocar")
        assert visao._p.lampada.get_style_context().has_class("moa-acesa") == ctx.radio.tocando
    assert nomes == {"Tocar", "Pausar"}


def test_trocar_de_disco_troca_so_a_capa_e_os_textos(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    corpo, capa = visao._p.corpo, visao._p.capa
    ctx.radio.abrir_disco(ctx.discos[1])
    assert visao._p.corpo is corpo and visao._p.capa is not capa
    assert f"Disco: {ctx.discos[1].title}" in textos(visao._p.corpo)


def test_o_foco_nao_pula_quando_so_o_volume_muda(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    visao = conteudo.telas[Tela.RADIO]
    original = visao.foco_inicial
    entregues = []
    visao.foco_inicial = lambda: entregues.append(original()) or entregues[-1]    # o que a janela recebe

    ctx.radio.volume_mais()
    assert entregues[-1] is None              # o foco fica no botão que o usuário apertou
    antes = len(entregues)
    ctx.radio.alternar()                      # troca Tocar por Pausar: o botão novo recebe o foco
    girar(0.3)                                # o estado do som chega um instante depois
    assert any(e is visao.botao_principal for e in entregues[antes:])
    ctx.radio.volume_menos()
    assert entregues[-1] is None
    ctx.session.ir_para(Tela.ESTANTE)
    ctx.session.ir_para(Tela.RADIO)           # chegar na tela de novo leva o foco ao Tocar/Pausar
    assert entregues[-1] is visao.botao_principal


def test_a_nota_do_visor_so_aparece_quando_ha_o_que_dizer(app):
    ctx, conteudo = app
    _abrir_no_radio(ctx)
    p = conteudo.telas[Tela.RADIO]._p
    assert not p.nota.get_visible()
    ctx.radio.nota = "Este é o fim do disco."
    ctx.session.ir_para(Tela.RADIO)
    conteudo.redesenhar()
    assert p.nota.get_visible() and p.nota.get_text() == "Este é o fim do disco."
