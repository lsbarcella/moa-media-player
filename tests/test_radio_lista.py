# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""A lista de músicas do rádio não pode ser refeita a cada clique de volume.

Num disco com centenas de músicas (a coleção do usuário tem uma pasta com 371),
refazer a lista a cada clique travava a tela. Aqui se confere QUANDO ela é refeita.
"""

import gi
import pytest

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.session import Tela
from moa.ui import widgets
from tests.test_ui_smoke import app, musica, montar  # noqa: F401  (fixtures)
from tests.ui_ajuda import girar, nome_do_botao, tem_display, textos, todos_os_widgets

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
    assert p.botao_volume.degrau == degrau
    ctx.player.definir_degrau_de_volume(10)
    ctx.radio.volume_menos(); ctx.radio.volume_mais()
    assert nome_do_botao(p.mais) == "Volume no máximo" and p.mais.get_style_context().has_class("moa-inativo")
    assert not textos(p.mais)                       # só o símbolo: sem texto visível (ADR-0025)
    ctx.player.definir_degrau_de_volume(0)
    ctx.radio.volume_menos()
    assert nome_do_botao(p.menos) == "Volume no mínimo"


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
    assert any(ctx.discos[1].title in t for t in textos(visao._p.corpo))


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


# -- discos grandes são montados em pedaços ----------------------------------------------------

@pytest.fixture
def disco_grande(tmp_path, make_track):
    raiz = tmp_path / "grande"
    for n in range(1, 151):
        make_track(raiz / "MIX", f"{n:03d}.mp3", title=f"Musica {n}", album="MIX",
                   artist="Ana", albumartist="Ana", tracknumber=str(n))
    ctx, conteudo = montar(tmp_path, raiz)
    yield ctx, conteudo
    ctx.encerrar()
    ctx.banco.close()


def _esperar_a_lista(visao, total):
    from tests.ui_ajuda import girar
    for _ in range(200):
        if len(visao._linhas) >= total and not visao._construtor_da_lista.pendente:
            return
        girar(0.05)
    raise AssertionError(f"a lista parou em {len(visao._linhas)} de {total} linhas")


def test_disco_grande_mostra_as_primeiras_linhas_e_completa_depois(disco_grande):
    ctx, conteudo = disco_grande
    ctx.radio.abrir_disco(ctx.discos[0])
    ctx.session.ir_para(Tela.RADIO)
    visao = conteudo.telas[Tela.RADIO]
    assert 30 <= len(visao._linhas) <= 150           # as primeiras já estão na tela
    _esperar_a_lista(visao, 150)
    assert len(visao._linhas) == 150
    assert "Musica 150" in textos(visao._lista)
    assert "Mexer neste disco" in [t for b in botoes_(visao._lista) for t in textos(b)]


def botoes_(raiz):
    from tests.ui_ajuda import botoes
    return botoes(raiz)


def test_o_botao_mexer_no_disco_fica_no_fim_mesmo_com_a_lista_incompleta(disco_grande):
    ctx, conteudo = disco_grande
    ctx.radio.abrir_disco(ctx.discos[0])
    ctx.session.ir_para(Tela.RADIO)
    visao = conteudo.telas[Tela.RADIO]
    _esperar_a_lista(visao, 150)
    filhos = visao._lista.get_children()
    assert "Mexer neste disco" in textos(filhos[-1]) and "Músicas deste disco" in textos(filhos[0])
    assert filhos.index(visao._linhas[0][0]) == 1 and filhos.index(visao._linhas[-1][0]) == len(filhos) - 2


def test_trocar_de_faixa_antes_de_a_linha_existir_marca_quando_ela_chegar(disco_grande):
    ctx, conteudo = disco_grande
    ctx.radio.abrir_disco(ctx.discos[0])
    ctx.session.ir_para(Tela.RADIO)
    visao = conteudo.telas[Tela.RADIO]
    assert len(visao._linhas) < 150
    ctx.radio.tocar_faixa(140)                       # uma linha que ainda não foi montada
    ctx.player.pausar()                              # (o som de teste acaba rápido e seguiria andando)
    _esperar_a_lista(visao, 150)
    from tests.ui_ajuda import girar
    girar(0.5)                                       # deixa as mensagens do som que já estavam a caminho
    atual = ctx.player.indice
    assert atual >= 140
    marcadas = [i for i, (_m, nomes) in enumerate(visao._linhas)
                if {"Tocando agora", "Parado aqui"} & set(textos(nomes))]
    assert marcadas == [atual]
    destacadas = [i for i, (m, _n) in enumerate(visao._linhas) if m.get_style_context().has_class("moa-agora")]
    assert destacadas == [atual]


def test_trocar_de_disco_no_meio_da_montagem_cancela_a_antiga(disco_grande):
    ctx, conteudo = disco_grande
    ctx.radio.abrir_disco(ctx.discos[0])
    ctx.session.ir_para(Tela.RADIO)
    visao = conteudo.telas[Tela.RADIO]
    antigo = visao._construtor_da_lista
    assert antigo.pendente
    ctx.radio.abrir_disco(ctx.discos[0], indice=3)   # mesmo disco, outra faixa: lista é reaproveitada
    assert visao._construtor_da_lista is antigo
    ctx.session.voltar_para_a_estante()
    ctx.radio.guardar_o_disco_e_parar()              # sem disco no rádio: a montagem para
    assert not antigo.pendente


def test_o_visor_do_radio_mostra_artista_album_e_ano_numa_linha_e_a_faixa_na_outra(app):
    from dataclasses import replace
    ctx, conteudo = app
    disco = replace(ctx.discos[0], artist="Ana", year=2005)
    ctx.radio.abrir_disco(disco, tocar=False)
    ctx.session.ir_para(Tela.RADIO)
    t = textos(conteudo.telas[Tela.RADIO]._p.corpo)
    assert f"Ana · {disco.title} · 2005" in t
    assert any(x.startswith("Faixa 1 de") for x in t)


def test_o_visor_nao_inventa_ano_quando_nao_ha(app):
    ctx, conteudo = app
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    ctx.session.ir_para(Tela.RADIO)
    assert not any(x.rstrip().endswith(" · 0") or x.endswith("None") for x in textos(conteudo.telas[Tela.RADIO]._p.corpo))


def test_em_letra_maior_e_tela_de_notebook_o_volume_cabe_na_primeira_tela(app):
    """O básico (estado, música, progresso, teclas e volume) tem de aparecer sem rolar em 1366x768."""
    ctx, conteudo = app
    ctx.preferencias.mudar(letra="maior")
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    ctx.session.ir_para(Tela.RADIO)
    janela = Gtk.OffscreenWindow()
    janela.set_size_request(1366, 768)
    janela.add(conteudo.raiz)
    janela.show_all()
    girar(0.6)
    legenda = next(w for w in todos_os_widgets(conteudo.raiz)
                   if isinstance(w, Gtk.Label) and w.get_text().startswith("Volume:"))
    _, y = legenda.translate_coordinates(janela, 0, 0)
    fim = y + legenda.get_allocated_height()
    janela.remove(conteudo.raiz)
    janela.destroy()
    assert fim <= 768, fim
