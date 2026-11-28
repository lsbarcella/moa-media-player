# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""O cartão da atualização de teste (ADR-0020) na Estante e em Configurações."""

import pytest

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
    assert any("Abrir de novo agora" in textos(b) for b in botoes(estante))
    assert "Pronto! Para usar a versão nova, o app precisa abrir de novo." in textos(estante)


def test_desligada_nao_mostra_nada(ativa):
    ctx, conteudo = ativa
    ctx.atualizacao.raiz = type(ctx.atualizacao.raiz)("/usr/lib/moa")
    ctx.atualizacao._mudar(Momento.HA_NOVA)
    assert "Atualização do app (versão de teste)" not in textos(conteudo.telas[Tela.ESTANTE].raiz)
