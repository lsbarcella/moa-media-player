# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes do log em arquivo e do gancho de exceções (M5)."""

import logging
import sys
import threading

import pytest

from moa.core import logsetup


@pytest.fixture(autouse=True)
def restaurar_log():
    raiz = logging.getLogger()
    antes = list(raiz.handlers)
    nivel = raiz.level
    gancho, gancho_thread = sys.excepthook, threading.excepthook
    yield
    for h in list(raiz.handlers):
        if h not in antes:
            raiz.removeHandler(h)
            h.close()
    raiz.setLevel(nivel)
    sys.excepthook, threading.excepthook = gancho, gancho_thread


def test_cria_a_pasta_e_grava_no_arquivo(tmp_path):
    pasta = tmp_path / "ainda" / "nao" / "existe"
    caminho = logsetup.configurar_log(pasta)
    logging.getLogger("moa.teste").warning("olá do teste")
    assert caminho == pasta / "moa.log"
    assert "olá do teste" in caminho.read_text(encoding="utf-8")


def test_configurar_duas_vezes_nao_duplica_linhas(tmp_path):
    logsetup.configurar_log(tmp_path)
    caminho = logsetup.configurar_log(tmp_path)
    logging.getLogger("moa.teste").warning("uma só vez")
    assert caminho.read_text(encoding="utf-8").count("uma só vez") == 1


def test_o_log_nao_cresce_sem_limite(tmp_path, monkeypatch):
    monkeypatch.setattr(logsetup, "TAMANHO_MAXIMO", 2000)
    caminho = logsetup.configurar_log(tmp_path)
    for i in range(500):
        logging.getLogger("moa.teste").warning("linha %d com algum texto para encher", i)
    arquivos = list(tmp_path.glob("moa.log*"))
    assert len(arquivos) <= logsetup.COPIAS_ANTIGAS + 1
    assert all(a.stat().st_size < 4000 for a in arquivos)
    assert caminho.exists()


def test_pasta_sem_permissao_nao_derruba_o_app(tmp_path):
    arquivo = tmp_path / "arquivo"
    arquivo.write_text("não sou pasta")
    assert logsetup.configurar_log(arquivo / "dentro") is None


def test_excecao_nao_tratada_vai_para_o_log_e_avisa(tmp_path):
    caminho = logsetup.configurar_log(tmp_path)
    avisos = []
    logsetup.instalar_gancho_de_excecao(lambda: avisos.append(1))
    try:
        raise ValueError("estourou de propósito")
    except ValueError:
        sys.excepthook(*sys.exc_info())
    texto = caminho.read_text(encoding="utf-8")
    assert "estourou de propósito" in texto and "Traceback" in texto
    assert avisos == [1]


def test_falha_ao_avisar_nao_causa_outra_falha(tmp_path):
    caminho = logsetup.configurar_log(tmp_path)

    def quebrado():
        raise RuntimeError("o aviso também quebrou")

    logsetup.instalar_gancho_de_excecao(quebrado)
    try:
        raise ValueError("primeira")
    except ValueError:
        sys.excepthook(*sys.exc_info())        # não pode lançar
    assert "o aviso também quebrou" in caminho.read_text(encoding="utf-8")


def test_excecao_em_outra_thread_tambem_e_registrada(tmp_path):
    caminho = logsetup.configurar_log(tmp_path)
    avisos = []
    logsetup.instalar_gancho_de_excecao(lambda: avisos.append(1))

    def trabalho():
        raise KeyError("na thread")

    t = threading.Thread(target=trabalho)
    t.start()
    t.join()
    assert "na thread" in caminho.read_text(encoding="utf-8")
    assert avisos == [1]
