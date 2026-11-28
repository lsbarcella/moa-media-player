# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""A Estante só é refeita quando algo que ela mostra muda, e discos demais vêm em pedaços."""

import pytest

from moa.core.session import Tela
from tests.test_ui_smoke import montar
from tests.ui_ajuda import girar, tem_display, textos, todos_os_widgets

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


@pytest.fixture
def estante_cheia(tmp_path, make_track):
    raiz = tmp_path / "estante"
    for n in range(1, 61):
        make_track(raiz / f"Disco {n:02d}", "01.mp3", title=f"Musica {n}", album=f"Disco {n:02d}",
                   artist="Ana", albumartist="Ana", tracknumber="1")
    ctx, conteudo = montar(tmp_path, raiz)
    yield ctx, conteudo, conteudo.telas[Tela.ESTANTE]
    ctx.encerrar()
    ctx.banco.close()


def _discos_na_tela(visao):
    return [t for t in textos(visao.raiz) if t.startswith("Disco ")]


def _esperar(visao):
    for _ in range(300):
        if not any(c.pendente for c in visao._construtores):
            return
        girar(0.05)
    raise AssertionError("a estante não terminou de ser montada")


def test_estante_grande_mostra_os_primeiros_e_completa(estante_cheia):
    ctx, conteudo, visao = estante_cheia
    assert 24 <= len(_discos_na_tela(visao)) <= 60
    _esperar(visao)
    nomes = _discos_na_tela(visao)
    assert len(nomes) == 60 and "Disco 60" in nomes


def test_nao_refaz_a_estante_quando_nada_mudou(estante_cheia):
    ctx, conteudo, visao = estante_cheia
    _esperar(visao)
    filhos = list(visao.raiz.get_children())
    for _ in range(5):
        conteudo.redesenhar()
    assert list(visao.raiz.get_children()) == filhos           # os mesmos widgets


def test_refaz_quando_a_colecao_muda(estante_cheia):
    ctx, conteudo, visao = estante_cheia
    _esperar(visao)
    filhos = list(visao.raiz.get_children())
    ctx.recarregar()
    assert list(visao.raiz.get_children()) != filhos


def test_refaz_com_aviso_com_disco_no_radio_e_durante_a_copia(estante_cheia):
    ctx, conteudo, visao = estante_cheia
    _esperar(visao)
    filhos = list(visao.raiz.get_children())
    ctx.session.mostrar_aviso("Teste de aviso")
    assert "Teste de aviso" in textos(visao.raiz) and list(visao.raiz.get_children()) != filhos
    ctx.session.acao()
    assert "Teste de aviso" not in textos(visao.raiz)
    ctx.radio.abrir_disco(ctx.discos[0])
    ctx.session.voltar_para_a_estante()
    assert "Em uso no rádio" in textos(visao.raiz)
    from moa.core.aparelho import Momento
    ctx.aparelho.momento = Momento.COPIANDO
    conteudo.redesenhar()
    assert "Ver a cópia do disco" in [t for w in todos_os_widgets(visao.raiz) if hasattr(w, "get_label")
                                      for t in [w.get_label()] if t]


def test_o_foco_nao_pula_quando_a_estante_nao_mudou(estante_cheia):
    ctx, conteudo, visao = estante_cheia
    original = visao.foco_inicial
    entregues = []
    visao.foco_inicial = lambda: entregues.append(original()) or entregues[-1]
    conteudo.redesenhar()
    assert entregues[-1] is None
    ctx.session.ir_para(Tela.CAIXA)
    ctx.session.ir_para(Tela.ESTANTE)
    assert entregues[-1] is not None            # voltou para a estante: o foco vai ao botão principal


def test_um_disco_que_falha_ao_desenhar_nao_esconde_os_outros(estante_cheia, monkeypatch):
    ctx, conteudo, visao = estante_cheia
    original = visao._peca

    def peca_quebrada(disco):
        if disco.title == "Disco 03":
            raise RuntimeError("capa ilegível")
        return original(disco)
    monkeypatch.setattr(visao, "_peca", peca_quebrada)
    ctx.recarregar()
    _esperar(visao)
    nomes = _discos_na_tela(visao)
    assert "Disco 03" not in nomes and len(nomes) == 59 and "Disco 04" in nomes and "Disco 60" in nomes


def test_se_o_desenho_falhar_a_proxima_vez_tenta_de_novo(estante_cheia, monkeypatch):
    ctx, conteudo, visao = estante_cheia
    _esperar(visao)

    def quebra():
        raise RuntimeError("falha qualquer")
    monkeypatch.setattr(visao, "_desenhar_acoes", quebra)
    visao._esquecer_o_desenho()
    with pytest.raises(RuntimeError):
        visao.atualizar()
    assert visao._chave_desenhada is None            # o desenho incompleto não vale como "pronto"
    monkeypatch.undo()
    visao.atualizar()
    assert visao._chave_desenhada is not None and len(_discos_na_tela(visao)) >= 24


def test_criar_uma_playlist_nao_esconde_nenhum_disco_nem_playlist(tmp_path, make_track):
    """O relato do autor: depois de criar uma playlist, sumiram o MIX e as outras playlists."""
    from moa.core import custom_albums
    raiz = tmp_path / "musica"
    for n in range(1, 41):
        make_track(raiz / "MIX", f"{n:03d}.mp3", title=f"Faixa {n}", album="MIX", artist="Ana",
                   albumartist="Ana", tracknumber=str(n))
    ctx, conteudo = montar(tmp_path, raiz)
    try:
        mix = ctx.discos[0]
        caminhos = [str(t.path) for t in mix.tracks]
        custom_albums.criar(ctx.banco, "Festa", caminhos[:3])
        custom_albums.criar(ctx.banco, "Dormir", caminhos[5:8])
        ctx.recarregar()
        ctx.radio.abrir_disco(mix)                       # o MIX está tocando
        ctx.session.voltar_para_a_estante()
        ctx.session.acao()
        ctx.novo_rascunho()
        ctx.session.ir_para(Tela.PLAYLIST)
        playlist = conteudo.telas[Tela.PLAYLIST]
        _esperar_playlist(playlist)
        for caminho in list(playlist._linhas)[:3]:
            playlist._linhas[caminho][0].clicked()
        playlist._guardar()
        est = conteudo.telas[Tela.ESTANTE]
        _esperar(est)
        girar(0.3)
        assert [d.title for d in ctx.discos] == ["MIX"]
        titulos = [d.title for d in ctx.montados]
        assert len(titulos) == 3 and {"Festa", "Dormir"} <= set(titulos)
        assert any(t.startswith("Meu disco de") for t in titulos)
        tela = textos(est.raiz)
        for esperado in ("Meus discos", "Discos que montei", "Festa", "Dormir"):
            assert esperado in tela
        assert len([t for t in tela if t.startswith("Meu disco de")]) == 1
    finally:
        ctx.encerrar()
        ctx.banco.close()


def _esperar_playlist(playlist):
    for _ in range(200):
        if playlist._linhas and not playlist._construtor_da_lista.pendente:
            return
        girar(0.05)
