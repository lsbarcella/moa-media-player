# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes de `state.py` (M2): onde parou e recentes."""

import sqlite3

import pytest

from moa.core.db import Database
from moa.core.state import Memoria, OndeParou


@pytest.fixture
def banco(tmp_path):
    b = Database(tmp_path / "moa.db")
    yield b
    b.close()


def test_gravar_a_posicao_e_reabrir_devolve_tudo_igual(tmp_path):
    caminho = tmp_path / "moa.db"
    primeiro = Database(caminho)
    Memoria(primeiro).guardar_onde_parou("/m/CD", 4, 73.25)
    primeiro.close()
    segundo = Database(caminho)
    try:
        assert Memoria(segundo).onde_parou({"/m/CD"}) == OndeParou("/m/CD", 4, 73.25)
    finally:
        segundo.close()


def test_disco_guardado_que_sumiu_devolve_nada(banco):
    memoria = Memoria(banco)
    memoria.guardar_onde_parou("/m/Sumiu", 1, 5.0)
    assert memoria.onde_parou({"/m/Outro"}) is None


def test_nunca_tocou_devolve_nada(banco):
    assert Memoria(banco).onde_parou({"/m/CD"}) is None


def test_recentes_no_maximo_5_na_estante_e_so_os_que_existem(banco):
    memoria = Memoria(banco)
    for nome in "ABCDEFG":
        memoria.registrar_recente(f"/m/{nome}")
    todos = {f"/m/{n}" for n in "ABCDEFG"}
    assert memoria.recentes(todos) == ["/m/G", "/m/F", "/m/E", "/m/D", "/m/C"]
    assert memoria.recentes(todos - {"/m/G"}) == ["/m/F", "/m/E", "/m/D", "/m/C", "/m/B"]


def test_gravacao_com_banco_ocupado_so_vai_para_o_log(tmp_path, caplog):
    caminho = tmp_path / "moa.db"
    memoria = Memoria(Database(caminho, timeout=0.1))
    # Outro "processo" segura o banco com uma gravação aberta.
    trava = sqlite3.connect(caminho, isolation_level=None)
    trava.execute("BEGIN IMMEDIATE")
    try:
        memoria.guardar_onde_parou("/m/CD", 1, 1.0)       # não pode levantar
        memoria.registrar_recente("/m/CD")
    finally:
        trava.execute("ROLLBACK")
        trava.close()
    assert "não consegui guardar" in caplog.text
