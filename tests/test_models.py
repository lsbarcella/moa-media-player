# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from moa.core.models import VARIOS_ARTISTAS, Album, Track


def faixa(nome_arquivo, numero=None):
    return Track(path=Path("/musica/disco") / nome_arquivo, title=nome_arquivo, number=numero)


def test_faixas_com_numero_vem_pelo_numero():
    faixas = [faixa("c.mp3", 3), faixa("a.mp3", 1), faixa("b.mp3", 2)]
    assert [t.number for t in sorted(faixas, key=lambda t: t.sort_key)] == [1, 2, 3]


def test_faixas_sem_numero_vem_pela_ordem_natural_do_nome():
    faixas = [faixa("Faixa 10.mp3"), faixa("Faixa 2.mp3"), faixa("Faixa 1.mp3")]
    nomes = [t.path.name for t in sorted(faixas, key=lambda t: t.sort_key)]
    assert nomes == ["Faixa 1.mp3", "Faixa 2.mp3", "Faixa 10.mp3"]


def test_faixas_com_numero_vem_antes_das_sem_numero():
    faixas = [faixa("sem numero.mp3"), faixa("z.mp3", 1)]
    nomes = [t.path.name for t in sorted(faixas, key=lambda t: t.sort_key)]
    assert nomes == ["z.mp3", "sem numero.mp3"]


def test_faixa_e_imutavel():
    t = faixa("a.mp3", 1)
    with pytest.raises(FrozenInstanceError):
        t.title = "outro"


def test_mesma_musica_em_dois_cds_sao_duas_faixas():
    a = Track(path=Path("/m/CD1/01.mp3"), title="Samba da Esquina")
    b = Track(path=Path("/m/CD2/05.mp3"), title="Samba da Esquina")
    assert a != b


def test_id_do_disco_e_o_caminho_da_pasta():
    assert Album(folder=Path("/m/Boleros"), title="Boleros").id == "/m/Boleros"


def test_estante_ordena_por_artista_e_depois_por_album():
    discos = [
        Album(folder=Path("/m/a"), title="Volume 2", artist="Beto"),
        Album(folder=Path("/m/b"), title="Volume 1", artist="Beto"),
        Album(folder=Path("/m/c"), title="Único", artist="Alberto"),
    ]
    titulos = [d.title for d in sorted(discos, key=lambda d: d.sort_key)]
    assert titulos == ["Único", "Volume 1", "Volume 2"]


def test_estante_ignora_acento_na_ordem_dos_artistas():
    discos = [
        Album(folder=Path("/m/a"), title="x", artist="Zé"),
        Album(folder=Path("/m/b"), title="y", artist="Álvaro"),
        Album(folder=Path("/m/c"), title="z", artist="Beto"),
    ]
    artistas = [d.artist for d in sorted(discos, key=lambda d: d.sort_key)]
    assert artistas == ["Álvaro", "Beto", "Zé"]


def test_disco_sem_artista_e_ordenado_pelo_proprio_nome():
    discos = [
        Album(folder=Path("/m/a"), title="Boleros"),  # sem artista
        Album(folder=Path("/m/b"), title="x", artist="Alberto"),
        Album(folder=Path("/m/c"), title="y", artist="Carlos"),
    ]
    nomes = [d.title for d in sorted(discos, key=lambda d: d.sort_key)]
    assert nomes == ["x", "Boleros", "y"]


def test_coletaneas_ficam_em_varios_artistas():
    discos = [
        Album(folder=Path("/m/a"), title="Sucessos", artist=VARIOS_ARTISTAS),
        Album(folder=Path("/m/b"), title="x", artist="Zeca"),
        Album(folder=Path("/m/c"), title="y", artist="Alberto"),
    ]
    artistas = [d.artist for d in sorted(discos, key=lambda d: d.sort_key)]
    assert artistas == ["Alberto", VARIOS_ARTISTAS, "Zeca"]


def test_discos_com_numero_no_nome_seguem_ordem_natural():
    discos = [
        Album(folder=Path("/m/a"), title="Sucessos Vol 10", artist="X"),
        Album(folder=Path("/m/b"), title="Sucessos Vol 2", artist="X"),
    ]
    nomes = [d.title for d in sorted(discos, key=lambda d: d.sort_key)]
    assert nomes == ["Sucessos Vol 2", "Sucessos Vol 10"]
