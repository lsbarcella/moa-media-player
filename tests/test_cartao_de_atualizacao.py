# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""O cartão da atualização de teste (ADR-0020) na Estante e em Configurações."""

import pytest

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.atualizacao_de_teste import Momento
from moa.core.session import Tela
from tests.test_ui_smoke import app, musica, montar  # noqa: F401  (fixtures)
from tests.ui_ajuda import botao_com_texto, botoes, textos, tem_display

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


@pytest.fixture
def ativa(app):
    ctx, conteudo = app
    ctx.atualizacao._buscar_commit = lambda: "b" * 40
    assert ctx.atualizacao.habilitada
    return ctx, conteudo


def test_configuracoes_mostra_o_cartao_com_o_botao_de_procurar(ativa):
    ctx, conteudo = ativa
    ctx.session.ir_para(Tela.CONFIGURACOES)
    raiz = conteudo.telas[Tela.CONFIGURACOES].raiz
    assert "Atualização do app (versão de teste)" in textos(raiz)
    botao_com_texto(raiz, "Procurar versão nova").clicked()
    ctx.atualizacao.thread.join(10)
    from tests.ui_ajuda import girar
    girar(0.2)
    assert ctx.atualizacao.momento in (Momento.HA_NOVA, Momento.ATUALIZADO)


def test_estante_so_mostra_o_cartao_quando_ha_algo_a_fazer(ativa):
    ctx, conteudo = ativa
    estante = conteudo.telas[Tela.ESTANTE].raiz
    assert "Atualização do app (versão de teste)" not in textos(estante)
    ctx.atualizacao.commit_remoto = "b" * 40
    ctx.atualizacao._mudar(Momento.HA_NOVA)
    assert "Atualização do app (versão de teste)" in textos(estante)
    assert any("Atualizar agora" in textos(b) for b in botoes(estante))


def test_pronto_oferece_abrir_de_novo(ativa):
    ctx, conteudo = ativa
    ctx.atualizacao._mudar(Momento.PRONTO)
    estante = conteudo.telas[Tela.ESTANTE].raiz
    assert any("Reiniciar o Aplicativo" in textos(b) for b in botoes(estante))
    assert any(x.startswith("Pronto! A versão nova está instalada") for x in textos(estante))


def test_desligada_nao_mostra_nada(ativa):
    ctx, conteudo = ativa
    ctx.atualizacao.raiz = type(ctx.atualizacao.raiz)("/usr/lib/moa")
    ctx.atualizacao._mudar(Momento.HA_NOVA)
    assert "Atualização do app (versão de teste)" not in textos(conteudo.telas[Tela.ESTANTE].raiz)


# -- o feedback do download e da instalação ------------------------------------------------------

def _cartao_da_estante(conteudo):
    from tests.ui_ajuda import todos_os_widgets
    estante = conteudo.telas[Tela.ESTANTE].raiz
    return [w for w in todos_os_widgets(estante)
            if "Atualização do app (versão de teste)" in textos(w) and isinstance(w, Gtk.Box)
            and w.get_style_context().has_class("moa-cartao")][0]


def _barra(cartao):
    from tests.ui_ajuda import todos_os_widgets
    return next(w for w in todos_os_widgets(cartao) if isinstance(w, Gtk.ProgressBar))


def _botao_de_reiniciar(cartao):
    from tests.ui_ajuda import todos_os_widgets
    return next(w for w in todos_os_widgets(cartao)
                if isinstance(w, Gtk.Button) and "Reiniciar o Aplicativo" in textos(w))


def test_versao_nova_mostra_o_tamanho_aproximado(ativa):
    ctx, conteudo = ativa
    ctx.atualizacao.commit_remoto = "b" * 40
    ctx.atualizacao.tamanho_estimado = 1_300_000
    ctx.atualizacao._mudar(Momento.HA_NOVA)
    estante = conteudo.telas[Tela.ESTANTE].raiz
    assert "Tamanho aproximado: 1,2 MB (descompactado)" in textos(estante)
    assert any("Atualizar agora" in textos(b) for b in botoes(estante))


def test_baixando_mostra_etapas_barra_e_o_botao_ainda_travado(ativa):
    ctx, conteudo = ativa
    a = ctx.atualizacao
    a.commit_remoto = "b" * 40
    a.bytes_baixados = 120 * 1024
    a._mudar(Momento.BAIXANDO)
    cartao = _cartao_da_estante(conteudo)
    todos = textos(cartao)
    assert "→  Baixando a atualização: 120 KB" in todos
    assert "○  Instalar a versão nova" in todos and "○  Reiniciar o aplicativo" in todos
    assert "Baixado até agora: 120 KB" in todos
    assert _barra(cartao).get_visible()
    reiniciar = _botao_de_reiniciar(cartao)
    assert not reiniciar.get_sensitive()                       # visível, mas ainda não liberado
    assert reiniciar.get_style_context().has_class("moa-inativo")


def test_o_andamento_do_download_muda_so_o_texto_sem_refazer_o_cartao(ativa):
    ctx, conteudo = ativa
    a = ctx.atualizacao
    a.commit_remoto = "b" * 40
    a._mudar(Momento.BAIXANDO)
    cartao = _cartao_da_estante(conteudo)
    botao_antes = _botao_de_reiniciar(cartao)
    for kb in (10, 50, 200):
        a.bytes_baixados = kb * 1024
        a._progrediu()
        assert f"→  Baixando a atualização: {kb} KB" in textos(cartao)
    assert _cartao_da_estante(conteudo) is cartao and _botao_de_reiniciar(cartao) is botao_antes


def test_instalando_mostra_a_etapa_atual_e_enche_a_barra(ativa):
    ctx, conteudo = ativa
    a = ctx.atualizacao
    a.commit_remoto = "b" * 40
    a.tamanho_do_pacote = a.bytes_baixados = 336 * 1024
    a.etapa_da_instalacao, a.etapas_feitas = "trocando as ferramentas", 3
    a._mudar(Momento.INSTALANDO)
    cartao = _cartao_da_estante(conteudo)
    todos = textos(cartao)
    assert "✓  Atualização baixada (336 KB)" in todos
    assert "→  Instalando a versão nova: trocando as ferramentas" in todos
    assert "Tamanho da atualização: 336 KB" in todos
    assert _barra(cartao).get_fraction() == pytest.approx(0.75)
    assert not _botao_de_reiniciar(cartao).get_sensitive()


def test_pronto_libera_o_botao_de_reiniciar(ativa):
    ctx, conteudo = ativa
    a = ctx.atualizacao
    a.commit_remoto = "b" * 40
    a.tamanho_do_pacote = a.bytes_baixados = 336 * 1024
    a._mudar(Momento.INSTALANDO)
    assert not _botao_de_reiniciar(_cartao_da_estante(conteudo)).get_sensitive()
    a._mudar(Momento.PRONTO)
    cartao = _cartao_da_estante(conteudo)
    reiniciar = _botao_de_reiniciar(cartao)
    assert reiniciar.get_sensitive() and reiniciar.get_style_context().has_class("moa-pri")
    assert "✓  Versão nova instalada" in textos(cartao) and _barra(cartao).get_fraction() == 1.0


def test_o_cartao_para_de_ouvir_quando_e_destruido(ativa):
    ctx, conteudo = ativa
    a = ctx.atualizacao
    a._mudar(Momento.BAIXANDO)
    antes = len(a._ouvintes_do_progresso)
    a._mudar(Momento.HA_NOVA)              # a estante refaz o cartão: o antigo é destruído
    from tests.ui_ajuda import girar
    girar(0.1)
    assert len(a._ouvintes_do_progresso) <= antes + 1
    a._progrediu()                          # não quebra com cartões antigos
