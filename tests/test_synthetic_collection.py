# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes do gerador de coleção sintética (`tools/make_synthetic_collection.py`)."""

import importlib.util
from pathlib import Path

from moa.core.library import scan

_CAMINHO = Path(__file__).resolve().parent.parent / "tools" / "make_synthetic_collection.py"
_spec = importlib.util.spec_from_file_location("make_synthetic_collection", _CAMINHO)
gerador = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gerador)


def test_gera_o_numero_pedido_de_discos_e_faixas_e_a_varredura_le_tudo(tmp_path):
    total = gerador.gerar(tmp_path / "m", discos=10, faixas=4)
    assert total == 40
    discos = scan(tmp_path / "m")
    assert len(discos) == 10 and sum(len(d.tracks) for d in discos) == 40
    # Os discos sem tags (1 a cada 5) caem no fallback: o nome da pasta vira o do disco.
    assert any(d.title.startswith("CD ") for d in discos)
    assert any(d.artist == "Vários artistas" for d in discos)


def test_mesma_semente_mesma_colecao(tmp_path):
    gerador.gerar(tmp_path / "a", discos=5, faixas=3, semente=7)
    gerador.gerar(tmp_path / "b", discos=5, faixas=3, semente=7)
    nomes = lambda raiz: sorted(str(p.relative_to(raiz)) for p in raiz.rglob("*") if p.is_file())
    assert nomes(tmp_path / "a") == nomes(tmp_path / "b")
