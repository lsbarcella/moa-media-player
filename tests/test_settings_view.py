# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes da tela de Configurações e dos ícones (M3)."""

import gi
import pytest

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from moa.core.config import Preferencias, carregar  # noqa: E402
from moa.core.session import Tela  # noqa: E402
from moa.ui import theme  # noqa: E402
from moa.ui.widgets import NOMES_DOS_ICONES, PASTA_DOS_ICONES, icone  # noqa: E402
from tests.test_ui_smoke import app, montar, musica  # noqa: E402,F401  (fixtures)
from tests.ui_ajuda import botao_com_texto, botoes, desenhar, girar, textos, tem_display  # noqa: E402

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")


def test_todo_icone_existe_e_carrega_nas_duas_cores():
    arquivos = {p.stem for p in PASTA_DOS_ICONES.glob("*.svg")}
    assert arquivos == set(NOMES_DOS_ICONES)
    for nome in NOMES_DOS_ICONES:
        for cor, fundo in (("#1E1913", "#FFFFFF"), ("#FFFFFF", "#1E1913")):
            imagem = icone(nome, cor, fundo)
            assert imagem.get_pixbuf() is not None and imagem.get_pixbuf().get_width() == 32


def test_nenhum_botao_de_nenhuma_tela_fica_sem_texto(app):
    ctx, conteudo = app
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    for tela in Tela:
        if tela not in conteudo.telas:
            continue
        ctx.session.ir_para(tela)
        for b in botoes(conteudo.raiz):
            # Botões de disco e de faixa têm o nome como texto; todos precisam de algum.
            assert [t for t in textos(b) if t.strip()], f"botão sem texto na tela {tela}"


def test_botao_configuracoes_em_toda_tela_menos_na_propria(app):
    ctx, conteudo = app
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    for tela in (Tela.ESTANTE, Tela.RADIO):
        ctx.session.ir_para(tela)
        assert "Configurações" in [t for b in botoes(conteudo.cabecalho) for t in textos(b)]
    ctx.session.ir_para(Tela.CONFIGURACOES)
    assert "Configurações" not in [t for b in botoes(conteudo.cabecalho) for t in textos(b)]
    assert "Voltar para onde eu estava" in [t for b in botoes(conteudo.cabecalho) for t in textos(b)]


def test_escolher_grande_grava_e_sobrevive_a_reabrir(app, tmp_path):
    ctx, conteudo = app
    ctx.session.ir_para(Tela.CONFIGURACOES)
    botao_com_texto(conteudo.telas[Tela.CONFIGURACOES].raiz, "Grande").clicked()
    assert ctx.preferencias.config.letra == "grande"
    assert carregar(tmp_path / "config.json").letra == "grande"
    assert Preferencias(tmp_path / "config.json").config.letra == "grande"      # "reabrir"
    # A marca de escolhido (✓) vai para o botão certo.
    botao = botao_com_texto(conteudo.telas[Tela.CONFIGURACOES].raiz, "Grande")
    assert "✓" in textos(botao)


@pytest.mark.parametrize("paleta", list(theme.PALETAS))
def test_cada_paleta_aplica_sem_erro_e_mantem_o_contraste(app, paleta, tmp_path):
    ctx, conteudo = app
    ctx.session.ir_para(Tela.CONFIGURACOES)
    botao_com_texto(conteudo.telas[Tela.CONFIGURACOES].raiz, theme.ROTULOS_DAS_PALETAS[paleta]).clicked()
    assert ctx.preferencias.config.paleta == paleta
    desenhar(conteudo, tmp_path / f"{paleta}.png")
    assert all(theme.contraste(paleta, t, f) >= 7 for t, f in theme.PARES_DE_CONTRASTE)


def test_letra_grande_empilha_as_colunas_do_radio_e_a_tela_ainda_desenha(app, tmp_path):
    ctx, conteudo = app
    ctx.preferencias.mudar(letra="maior")
    ctx.radio.abrir_disco(ctx.discos[0], tocar=False)
    ctx.session.ir_para(Tela.RADIO)
    pixbuf = desenhar(conteudo, tmp_path / "maior.png")
    assert pixbuf.get_width() == 1100
    assert conteudo.telas[Tela.RADIO]._empilhado is True


def test_configuracao_corrompida_abre_com_os_padroes_sem_mensagem(tmp_path, musica):
    (tmp_path / "config.json").write_text("{lixo", encoding="utf-8")
    ctx, conteudo = montar(tmp_path, musica)
    try:
        assert ctx.preferencias.config.letra == "normal" and ctx.preferencias.config.paleta == "normal"
        assert ctx.session.aviso is None
    finally:
        ctx.encerrar(); ctx.banco.close()
