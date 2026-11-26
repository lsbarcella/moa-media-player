# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes dos discos montados (M4): virtuais, sem copiar arquivos."""

import logging
from datetime import date

import pytest

from moa.core import custom_albums as ca
from moa.core.db import Database
from moa.core.library import scan


@pytest.fixture
def db():
    banco = Database(":memory:")
    yield banco
    banco.close()


@pytest.fixture
def colecao(make_track, tmp_path):
    raiz = tmp_path / "musica"
    for album in ("Boleros", "Valsas"):
        for n in (1, 2, 3):
            make_track(raiz / album, f"{n:02d}.mp3", title=f"{album} {n}", album=album,
                       artist="Ana", tracknumber=str(n))
    discos = scan(raiz)
    faixas = {str(t.path): t for d in discos for t in d.tracks}
    return raiz, discos, faixas


def caminhos(colecao, *titulos):
    _, _, faixas = colecao
    por_titulo = {t.title: p for p, t in faixas.items()}
    return [por_titulo[t] for t in titulos]


def test_criar_com_3_faixas_devolve_as_3_na_ordem_escolhida(db, colecao):
    ordem = caminhos(colecao, "Valsas 2", "Boleros 1", "Boleros 3")
    mix_id = ca.criar(db, "Domingo", ordem)
    [disco] = ca.carregar(db, colecao[2])
    assert disco.id == mix_id and ca.eh_disco_montado(mix_id)
    assert disco.title == "Domingo"
    assert [t.title for t in disco.tracks] == ["Valsas 2", "Boleros 1", "Boleros 3"]


def test_criar_nao_repete_faixa_e_nome_vazio_ganha_um_padrao(db, colecao):
    a = caminhos(colecao, "Boleros 1")[0]
    ca.criar(db, "   ", [a, a])
    [disco] = ca.carregar(db, colecao[2])
    assert len(disco.tracks) == 1 and disco.title == "Meu disco"


def test_adicionar_faixa_ja_presente_nao_duplica_e_avisa(db, colecao):
    a, b = caminhos(colecao, "Boleros 1", "Valsas 1")
    mix_id = ca.criar(db, "Mix", [a])
    assert ca.adicionar_faixa(db, mix_id, b) is True
    assert ca.adicionar_faixa(db, mix_id, b) is False
    assert len(ca.carregar(db, colecao[2])[0].tracks) == 2


def test_desfazer_remove_a_ultima_faixa_ou_o_disco_recem_criado(db, colecao):
    a, b = caminhos(colecao, "Boleros 1", "Valsas 1")
    mix_id = ca.criar(db, "Mix", [a])
    ca.adicionar_faixa(db, mix_id, b)
    ca.remover_faixa(db, mix_id, b)
    assert [t.title for t in ca.carregar(db, colecao[2])[0].tracks] == ["Boleros 1"]
    ca.apagar(db, mix_id)
    assert ca.carregar(db, colecao[2]) == []


def test_apagar_o_montado_nao_toca_nas_musicas_dos_outros_discos(db, colecao):
    raiz, discos, faixas = colecao
    mix_id = ca.criar(db, "Mix", caminhos(colecao, "Boleros 1"))
    ca.apagar(db, mix_id)
    assert all(t.path.exists() for d in discos for t in d.tracks)


def test_faixa_cujo_arquivo_sumiu_da_colecao_e_pulada_e_vai_para_o_log(db, colecao, caplog):
    a, b = caminhos(colecao, "Boleros 1", "Valsas 1")
    ca.criar(db, "Mix", [a, b])
    sem_b = {p: t for p, t in colecao[2].items() if p != b}
    with caplog.at_level(logging.INFO):
        [disco] = ca.carregar(db, sem_b)
    assert [t.title for t in disco.tracks] == ["Boleros 1"]
    assert "não está mais na coleção" in caplog.text


def test_nome_sugerido_nao_repete():
    hoje = date(2026, 11, 26)
    assert ca.sugerir_nome([], hoje) == "Meu disco de 26/11"
    assert ca.sugerir_nome(["Meu disco de 26/11"], hoje) == "Meu disco de 26/11 (2)"
    assert ca.sugerir_nome(["Meu disco de 26/11", "Meu disco de 26/11 (2)"], hoje) == "Meu disco de 26/11 (3)"


def test_mix_com_zero_faixas_resolvidas_continua_existindo(db, colecao):
    ca.criar(db, "Vazio", caminhos(colecao, "Boleros 1"))
    [disco] = ca.carregar(db, {})
    assert disco.tracks == ()


# -- rascunho da playlist ------------------------------------------------------------------------

def test_rascunho_marcacoes_sobrevivem_ao_filtro_e_ao_limpar_o_filtro(colecao):
    _, discos, _ = colecao
    r = ca.RascunhoDePlaylist([], date(2026, 11, 26))
    a, b, c = (str(t.path) for t in (discos[0].tracks[0], discos[0].tracks[1], discos[1].tracks[0]))
    for caminho in (a, b, c):
        r.alternar(caminho)
    r.busca = "Valsas 1"
    assert [f.title for _, f in r.filtrar(discos)] == ["Valsas 1"]
    r.busca = ""
    assert len(r.filtrar(discos)) == 6 and r.marcadas == [a, b, c]
    r.alternar(b)
    assert r.marcadas == [a, c] and not r.esta_marcada(b)


def test_rascunho_filtra_por_disco_e_ignora_acentos_e_maiusculas(make_track, tmp_path):
    raiz = tmp_path / "m"
    make_track(raiz / "A", "01.mp3", title="Coração Valente", album="A")
    make_track(raiz / "B", "01.mp3", title="Outra", album="B")
    discos = scan(raiz)
    r = ca.RascunhoDePlaylist([])
    r.busca = "CORACAO"
    assert [f.title for _, f in r.filtrar(discos)] == ["Coração Valente"]
    r.busca = ""
    r.disco_do_filtro = next(d.id for d in discos if d.title == "B")
    assert [f.title for _, f in r.filtrar(discos)] == ["Outra"]


def test_rascunho_ja_nasce_com_nome_sugerido_sem_repetir():
    r = ca.RascunhoDePlaylist(["Meu disco de 26/11"], date(2026, 11, 26))
    assert r.nome == "Meu disco de 26/11 (2)"
