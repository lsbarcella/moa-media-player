# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes de `config.py` (M2): preferências em JSON."""

import json
import os

import pytest

from moa.core import config as cfg
from moa.core.config import Config


def test_sem_arquivo_devolve_os_padroes(tmp_path):
    c = cfg.carregar(tmp_path / "config.json")
    assert c == Config(letra="normal", paleta="normal", voz_mais_clara=False, volume=6)


def test_salvar_e_carregar_devolve_o_mesmo(tmp_path):
    caminho = tmp_path / "moa" / "config.json"
    original = Config(letra="maior", paleta="azul-amarelo", voz_mais_clara=True, volume=3)
    cfg.salvar(original, caminho)
    assert cfg.carregar(caminho) == original


def test_json_corrompido_volta_aos_padroes_e_guarda_o_arquivo_ruim(tmp_path):
    caminho = tmp_path / "config.json"
    caminho.write_text("{isto nao e json", encoding="utf-8")
    assert cfg.carregar(caminho) == Config()
    assert not caminho.exists()
    ruins = list(tmp_path.glob("config.json.problema-*"))
    assert len(ruins) == 1 and ruins[0].read_text() == "{isto nao e json"


def test_json_que_nao_e_objeto_tambem_e_tratado_como_corrompido(tmp_path):
    caminho = tmp_path / "config.json"
    caminho.write_text("[1, 2]", encoding="utf-8")
    assert cfg.carregar(caminho) == Config()


@pytest.mark.parametrize("campo,ruim", [
    ("letra", "gigante"), ("paleta", "rosa"), ("voz_mais_clara", "sim"),
    ("volume", 11), ("volume", -1), ("volume", True), ("volume", "5"),
])
def test_valor_fora_do_permitido_volta_ao_padrao_so_naquele_campo(tmp_path, campo, ruim):
    caminho = tmp_path / "config.json"
    caminho.write_text(json.dumps({"letra": "grande", "paleta": "preto-e-branco",
                                   "voz_mais_clara": True, "volume": 2, campo: ruim}))
    c = cfg.carregar(caminho)
    assert getattr(c, campo) == getattr(Config(), campo)
    outros = {"letra": "grande", "paleta": "preto-e-branco", "voz_mais_clara": True, "volume": 2}
    for nome, valor in outros.items():
        if nome != campo:
            assert getattr(c, nome) == valor


def test_falha_no_meio_da_gravacao_mantem_o_arquivo_antigo_e_nao_deixa_temporario(tmp_path, monkeypatch):
    caminho = tmp_path / "config.json"
    cfg.salvar(Config(letra="grande"), caminho)

    def quebrar(*_):
        raise OSError("energia caiu")

    monkeypatch.setattr(os, "replace", quebrar)
    with pytest.raises(OSError):
        cfg.salvar(Config(letra="maior"), caminho)
    monkeypatch.undo()
    assert cfg.carregar(caminho).letra == "grande"
    assert [p.name for p in tmp_path.iterdir()] == ["config.json"]
