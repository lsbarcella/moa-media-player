# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes de `session.py` (M3): navegação e avisos sem GTK."""

from moa.core.session import Session, Tela


def test_comeca_na_estante_sem_botao_de_voltar():
    s = Session()
    assert s.tela == Tela.ESTANTE and s.texto_de_voltar is None


def test_estante_radio_e_volta_para_a_estante():
    s = Session()
    s.ir_para(Tela.RADIO)
    assert s.tela == Tela.RADIO and s.anterior == Tela.ESTANTE
    assert s.texto_de_voltar == "Voltar para a estante"
    s.voltar_para_a_estante()
    assert s.tela == Tela.ESTANTE


def test_configuracoes_sempre_volta_para_onde_estava():
    s = Session()
    s.ir_para(Tela.RADIO)
    s.ir_para(Tela.CONFIGURACOES)
    assert s.texto_de_voltar == "Voltar para onde eu estava"
    s.voltar()
    assert s.tela == Tela.RADIO
    s.ir_para(Tela.CAIXA)
    s.ir_para(Tela.CONFIGURACOES)
    s.voltar()
    assert s.tela == Tela.CAIXA


def test_botao_configuracoes_em_toda_tela_menos_na_propria():
    s = Session()
    for tela in Tela:
        s.ir_para(tela)
        assert s.mostra_botao_configuracoes == (tela != Tela.CONFIGURACOES)


def test_aviso_fica_ate_a_proxima_acao_e_nao_some_sozinho():
    s = Session()
    s.mostrar_aviso("Guardei o disco.")
    assert s.aviso.texto == "Guardei o disco."      # continua lá, sem nenhuma ação
    s.acao()
    assert s.aviso is None


def test_mudar_de_tela_apaga_o_aviso():
    s = Session()
    s.mostrar_aviso("Oi")
    s.ir_para(Tela.RADIO)
    assert s.aviso is None


def test_desfazer_executa_a_acao_e_limpa_o_aviso_sem_passar_por_acao():
    s = Session()
    feito = []
    s.mostrar_aviso("Coloquei a música no disco.", desfazer=lambda: feito.append("desfeito"))
    s.desfazer()
    assert feito == ["desfeito"] and s.aviso is None


def test_ouvintes_sao_avisados_das_mudancas():
    s = Session()
    vezes = []
    s.ao_mudar(lambda: vezes.append(1))
    s.ir_para(Tela.RADIO)
    s.mostrar_aviso("x")
    s.acao()
    assert len(vezes) == 3
