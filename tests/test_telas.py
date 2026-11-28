# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes do gerador de imagens das telas (tools/telas.py, ADR-0024)."""

import importlib.util
from pathlib import Path

import pytest

from moa.ui import theme
from tests.ui_ajuda import tem_display

pytestmark = pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")

_CAMINHO = Path(__file__).resolve().parent.parent / "tools" / "telas.py"
_spec = importlib.util.spec_from_file_location("telas", _CAMINHO)
telas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(telas)


def test_as_seis_telas_da_aparencia_estao_na_lista():
    assert set(telas.TELAS) == {"estante", "radio", "aparelho-de-cd", "lixeira", "configuracoes", "playlist"}


def test_gera_uma_imagem_por_tela_nas_tres_escalas_de_uma_paleta(tmp_path):
    arquivos = telas.gerar(tmp_path, paletas=["normal"])
    assert len(arquivos) == 6 * 1 * len(theme.ESCALAS)
    assert all(a.exists() and a.stat().st_size > 2000 for a in arquivos)
    assert {a.name.split("__")[0] for a in arquivos} == set(telas.TELAS)


def test_a_paleta_preto_e_branco_gera_imagens_diferentes_da_normal(tmp_path):
    normal = telas.gerar(tmp_path / "n", paletas=["normal"], letras=["normal"], telas=["radio"])[0]
    pb = telas.gerar(tmp_path / "p", paletas=["preto-e-branco"], letras=["normal"], telas=["radio"])[0]
    assert normal.read_bytes() != pb.read_bytes()
