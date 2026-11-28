# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""A montagem de listas longas em pedaços (`EmPedacos`)."""

import time

from moa.ui.widgets import EmPedacos
from tests.ui_ajuda import girar


def test_lista_curta_termina_na_propria_chamada():
    feitos, fim = [], []
    EmPedacos(range(10), feitos.append, minimo=30, ao_terminar=lambda: fim.append(1)).iniciar()
    assert feitos == list(range(10)) and fim == [1]


def test_a_primeira_fatia_tem_pelo_menos_o_minimo():
    feitos = []

    def devagar(item):
        time.sleep(0.003)
        feitos.append(item)
    pedacos = EmPedacos(range(200), devagar, minimo=30, orcamento_ms=1).iniciar()
    assert 30 <= len(feitos) < 200 and pedacos.pendente
    pedacos.cancelar()


def test_o_resto_vem_depois_sem_prender_a_tela_e_na_ordem():
    feitos, fim = [], []

    def devagar(item):
        time.sleep(0.002)
        feitos.append(item)
    EmPedacos(range(120), devagar, minimo=10, orcamento_ms=5, ao_terminar=lambda: fim.append(1)).iniciar()
    assert len(feitos) < 120 and not fim
    for _ in range(100):
        girar(0.05)
        if fim:
            break
    assert feitos == list(range(120)) and fim == [1]


def test_cada_fatia_respeita_o_orcamento_de_tempo():
    duracoes, ultimo = [], [None]

    def devagar(item):
        time.sleep(0.002)
    pedacos = EmPedacos(range(200), devagar, minimo=5, orcamento_ms=8).iniciar()
    while pedacos.pendente:
        inicio = time.perf_counter()
        pedacos._continuar()
        duracoes.append(time.perf_counter() - inicio)
    assert max(duracoes) < 0.05                      # nenhuma fatia segura a tela por muito tempo


def test_cancelar_para_de_vez():
    feitos = []
    pedacos = EmPedacos(range(500), lambda i: (time.sleep(0.001), feitos.append(i)), minimo=5,
                        orcamento_ms=2).iniciar()
    parcial = len(feitos)
    pedacos.cancelar()
    girar(0.3)
    assert len(feitos) == parcial and not pedacos.pendente


def test_terminar_agora_faz_o_que_falta():
    feitos = []
    pedacos = EmPedacos(range(300), lambda i: (time.sleep(0.0005), feitos.append(i)),
                        minimo=5, orcamento_ms=1).iniciar()
    pedacos.terminar_agora()
    assert feitos == list(range(300)) and not pedacos.pendente


def test_um_item_que_falha_nao_impede_os_outros():
    feitos = []

    def fazer(i):
        if i == 3:
            raise ValueError("capa quebrada")
        feitos.append(i)
    EmPedacos(range(8), fazer, minimo=30).iniciar()
    assert feitos == [0, 1, 2, 4, 5, 6, 7]


def test_item_que_falha_em_uma_fatia_tardia_tambem_segue():
    feitos = []

    def fazer(i):
        time.sleep(0.001)
        if i == 70:
            raise ValueError("quebrou")
        feitos.append(i)
    pedacos = EmPedacos(range(100), fazer, minimo=5, orcamento_ms=3).iniciar()
    pedacos.terminar_agora()
    assert feitos == [i for i in range(100) if i != 70] and not pedacos.pendente
