# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes do carregador em segundo plano (M3)."""

import threading

import pytest

from moa.core.config import Preferencias
from moa.core.contexto import Contexto
from moa.core.db import Database
from moa.ui import loader as loader_mod
from moa.ui.loader import Carregador, varrer
from tests.test_player import esperar


@pytest.fixture
def musica(make_track, tmp_path):
    raiz = tmp_path / "musica"
    for album in ("Boleros", "Valsas"):
        for n in (1, 2):
            make_track(raiz / album, f"{n:02d}.mp3", title=f"{album} {n}", album=album, artist="Ana")
    return raiz


def test_varrer_devolve_discos_e_miniaturas_sem_gtk(musica, tmp_path):
    discos, miniaturas = varrer(tmp_path / "moa.db", musica, tmp_path / "min")
    assert sorted(d.title for d in discos) == ["Boleros", "Valsas"]
    assert set(miniaturas) == {d.id for d in discos}


def test_o_carregador_atualiza_a_estante_em_outra_thread_com_a_propria_conexao(musica, tmp_path, monkeypatch):
    threads = []
    original = loader_mod.Database

    class BancoQueAnotaAThread(original):
        def __init__(self, *args, **kwargs):
            threads.append(threading.current_thread().name)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(loader_mod, "Database", BancoQueAnotaAThread)
    banco = Database(tmp_path / "moa.db")
    ctx = Contexto(banco, Preferencias(tmp_path / "c.json"), musica)
    avisos = []
    ctx.ao_mudar_a_colecao(lambda: avisos.append(threading.current_thread().name))
    try:
        assert ctx.carregando and ctx.discos == []
        Carregador(ctx, tmp_path / "moa.db", tmp_path / "min").iniciar()
        # A janela segue viva: a conexão da thread principal continua usável durante a varredura.
        assert banco.load_tracks() is not None
        assert esperar(lambda: not ctx.carregando)
        assert sorted(d.title for d in ctx.discos) == ["Boleros", "Valsas"]
        assert threads == ["varredura"]                         # o Database da varredura nasceu nela
        assert avisos == [threading.main_thread().name]          # e a tela foi avisada na principal
    finally:
        ctx.encerrar(); banco.close()


def test_falha_na_varredura_nao_derruba_e_a_estante_deixa_de_carregar(tmp_path, monkeypatch, caplog):
    def quebrar(*_a, **_k):
        raise RuntimeError("disco sumiu")

    monkeypatch.setattr(loader_mod, "varrer", quebrar)
    banco = Database(tmp_path / "moa.db")
    ctx = Contexto(banco, Preferencias(tmp_path / "c.json"), tmp_path)
    try:
        Carregador(ctx, tmp_path / "moa.db", tmp_path / "min").iniciar()
        assert esperar(lambda: not ctx.carregando)
        assert ctx.discos == [] and "a varredura da pasta de música falhou" in caplog.text
    finally:
        ctx.encerrar(); banco.close()
