# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes da ferramenta de medição (`tools/measure.py`, ADR-0021)."""

import csv
import importlib.util
from pathlib import Path

import pytest

from moa.core.library import scan
from tests.ui_ajuda import tem_display

_CAMINHO = Path(__file__).resolve().parent.parent / "tools" / "measure.py"
_spec = importlib.util.spec_from_file_location("measure", _CAMINHO)
medir = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(medir)


def test_a_maquina_e_descrita_sem_dados_pessoais():
    maquina = medir.descrever_a_maquina()
    assert set(maquina) == {"cpu", "nucleos", "ram_mb", "disco", "so", "desktop", "python",
                            "gtk", "commit"}
    assert int(maquina["nucleos"]) >= 1 and int(maquina["ram_mb"]) > 0
    import getpass, socket
    texto = " ".join(maquina.values())
    assert getpass.getuser() not in texto and socket.gethostname() not in texto


def test_colecao_de_teste_e_lida_pela_biblioteca(tmp_path):
    base = medir.gerar_audio_base(tmp_path, buffers=4, nome="base")
    total = medir.gerar_colecao(tmp_path / "musica", base, discos=3, faixas=4, artista="Artista")
    discos = scan(tmp_path / "musica")
    assert total == 12 and len(discos) == 3 and all(len(d.tracks) == 4 for d in discos)
    assert discos[0].artist == "Artista" and discos[0].tracks[1].title == "Música 1-2"


def test_um_disco_so_com_muitas_faixas(tmp_path):
    base = medir.gerar_audio_base(tmp_path, buffers=4, nome="base")
    medir.gerar_colecao(tmp_path / "musica", base, discos=1, faixas=30, artista="Artista")
    discos = scan(tmp_path / "musica")
    assert len(discos) == 1 and len(discos[0].tracks) == 30


@pytest.mark.parametrize("metrica, valor, deve_passar", [
    ("abertura_1a_ms", 2900, True), ("abertura_1a_ms", 3100, False),
    ("abertura_seguinte_ms", 900, True), ("abertura_seguinte_ms", 1100, False),
    ("cpu_tocando_pct", 4.9, True), ("cpu_tocando_pct", 5.0, False),
])
def test_avalia_contra_as_metas_do_claude_md(metrica, valor, deve_passar):
    assert medir.avaliar(metrica, valor).startswith("OK") is deve_passar


def test_metrica_sem_meta_nao_tem_veredito():
    assert medir.avaliar("ram_repouso_mb", 90) == ""


def test_csv_tem_a_maquina_em_cada_linha(tmp_path):
    maquina = {"cpu": "X", "nucleos": "2", "ram_mb": "4096", "disco": "HDD", "so": "Mint",
               "desktop": "XFCE", "python": "3.10", "gtk": "3.24", "commit": "abc1234"}
    medir.gravar(tmp_path / "m.csv", maquina, [("mix", "abertura_1a_ms", 1234.5678, "ms")])
    linhas = list(csv.DictReader(open(tmp_path / "m.csv", encoding="utf-8")))
    assert linhas[0]["cpu"] == "X" and linhas[0]["disco"] == "HDD" and linhas[0]["commit"] == "abc1234"
    assert linhas[0]["cenario"] == "mix" and linhas[0]["valor"] == "1234.57"
    assert linhas[0]["data"].startswith("20")


@pytest.mark.skipif(not tem_display(), reason="sem sessão gráfica (DISPLAY)")
def test_abre_o_app_de_verdade_e_mede(tmp_path):
    if medir.moa_ja_aberto():
        pytest.skip("há um Moa aberto")
    cenarios = medir.montar_cenarios(tmp_path, rapido=True)
    ms, ram, cpu = medir.abrir_o_app(cenarios["mix"], tmp_path / "app")
    assert 0 < ms < 60_000 and 20 < ram < 1000 and 0 <= cpu < 100
