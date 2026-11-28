# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes do leitor de pastas e tags (M1, parte 2).

Usam arquivos de áudio de verdade, gerados no próprio teste (ver conftest.py).
"""

import pytest

from moa.core.library import read_track, scan, title_from_filename
from moa.core.models import VARIOS_ARTISTAS


# ---------------------------------------------------------------------------
# Fallback pelo nome do arquivo
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "nome, esperado",
    [
        ("Faixa 01", ("Faixa 1", 1)),
        ("faixa 7", ("Faixa 7", 7)),
        ("Faixa10", ("Faixa 10", 10)),
        ("01", ("Faixa 1", 1)),
        ("05 - Samba da Esquina", ("Samba da Esquina", 5)),
        ("05. Samba da Esquina", ("Samba da Esquina", 5)),
        ("12_Ponteio", ("Ponteio", 12)),
        ("Samba da Esquina", ("Samba da Esquina", None)),
        ("Samba_da_Esquina", ("Samba da Esquina", None)),
        ("1979 Blues", ("1979 Blues", None)),   # número sem separador faz parte do título
    ],
)
def test_titulo_e_numero_a_partir_do_nome_do_arquivo(nome, esperado):
    assert title_from_filename(nome) == esperado


# ---------------------------------------------------------------------------
# Leitura de uma faixa
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("extensao", [".mp3", ".flac", ".ogg"])
def test_le_tags_completas(tmp_path, make_track, extensao):
    arquivo = make_track(
        tmp_path / "disco", f"qualquer{extensao}",
        title="Samba da Esquina", artist="Zeca", album="Sambas",
        albumartist="Zeca", tracknumber="3",
    )
    t = read_track(arquivo)
    assert (t.title, t.artist, t.album, t.album_artist, t.number) == (
        "Samba da Esquina", "Zeca", "Sambas", "Zeca", 3)
    assert t.size > 0 and t.mtime > 0


def test_numero_da_faixa_no_formato_3_de_12(tmp_path, make_track):
    arquivo = make_track(tmp_path / "d", "a.mp3", title="X", tracknumber="3/12")
    assert read_track(arquivo).number == 3


def test_sem_tags_usa_o_nome_do_arquivo(tmp_path, make_track):
    arquivo = make_track(tmp_path / "d", "Faixa 01.mp3")
    t = read_track(arquivo)
    assert (t.title, t.number, t.artist, t.album) == ("Faixa 1", 1, None, None)


def test_sem_tag_de_titulo_mas_com_numero_no_nome(tmp_path, make_track):
    arquivo = make_track(tmp_path / "d", "05 - Samba da Esquina.flac")
    t = read_track(arquivo)
    assert (t.title, t.number) == ("Samba da Esquina", 5)


def test_arquivo_so_com_o_titulo(tmp_path, make_track):
    arquivo = make_track(tmp_path / "d", "Samba da Esquina.ogg")
    t = read_track(arquivo)
    assert (t.title, t.number) == ("Samba da Esquina", None)


def test_tag_tem_prioridade_sobre_o_nome_do_arquivo(tmp_path, make_track):
    arquivo = make_track(tmp_path / "d", "Faixa 01.mp3", title="Título da Tag", tracknumber="9")
    t = read_track(arquivo)
    assert (t.title, t.number) == ("Título da Tag", 9)


def test_arquivo_corrompido_nao_quebra(tmp_path):
    pasta = tmp_path / "d"
    pasta.mkdir()
    ruim = pasta / "03 - Quebrada.mp3"
    ruim.write_bytes(b"isto nao e um mp3 de verdade")
    t = read_track(ruim)
    assert (t.title, t.number) == ("Quebrada", 3)


def test_arquivo_vazio_nao_quebra(tmp_path):
    pasta = tmp_path / "d"
    pasta.mkdir()
    vazio = pasta / "Vazio.m4a"
    vazio.write_bytes(b"")
    assert read_track(vazio).title == "Vazio"


def test_tags_so_com_espacos_sao_ignoradas(tmp_path, make_track):
    arquivo = make_track(tmp_path / "d", "Faixa 02.mp3", title="   ")
    assert read_track(arquivo).title == "Faixa 2"


# ---------------------------------------------------------------------------
# Varredura: pastas e discos
# ---------------------------------------------------------------------------

def test_pasta_vira_disco_e_o_nome_da_pasta_vira_o_titulo(tmp_path, make_track):
    make_track(tmp_path / "Boleros", "01.mp3")
    make_track(tmp_path / "Boleros", "02.mp3")
    discos = scan(tmp_path)
    assert len(discos) == 1
    assert discos[0].title == "Boleros"
    assert discos[0].artist is None
    assert len(discos[0].tracks) == 2


def test_a_tag_de_album_vence_o_nome_da_pasta(tmp_path, make_track):
    make_track(tmp_path / "cd01", "a.mp3", album="Os Melhores Boleros")
    make_track(tmp_path / "cd01", "b.mp3", album="Os Melhores Boleros")
    assert scan(tmp_path)[0].title == "Os Melhores Boleros"


def test_se_as_tags_discordam_vale_a_mais_comum(tmp_path, make_track):
    make_track(tmp_path / "x", "a.mp3", album="Certo")
    make_track(tmp_path / "x", "b.mp3", album="Certo")
    make_track(tmp_path / "x", "c.mp3", album="Errado")
    assert scan(tmp_path)[0].title == "Certo"


def test_toda_pasta_com_audio_e_um_disco_em_qualquer_profundidade(tmp_path, make_track):
    make_track(tmp_path / "Zeca" / "Sambas", "01.mp3")
    make_track(tmp_path / "Beto" / "Valsas", "01.flac")
    make_track(tmp_path / "Solto", "01.ogg")
    titulos = sorted(d.title for d in scan(tmp_path))
    assert titulos == ["Sambas", "Solto", "Valsas"]


def test_pastas_sem_audio_sao_ignoradas(tmp_path, make_track):
    (tmp_path / "Fotos").mkdir()
    (tmp_path / "Fotos" / "praia.jpg").write_bytes(b"x")
    (tmp_path / "Documentos").mkdir()
    make_track(tmp_path / "Boleros", "01.mp3")
    assert [d.title for d in scan(tmp_path)] == ["Boleros"]


def test_arquivos_cda_sao_ignorados(tmp_path, make_track):
    make_track(tmp_path / "CD copiado", "01.mp3")
    (tmp_path / "CD copiado" / "Track01.cda").write_bytes(b"cda")
    (tmp_path / "So cda").mkdir()
    (tmp_path / "So cda" / "Track01.cda").write_bytes(b"cda")
    discos = scan(tmp_path)
    assert [d.title for d in discos] == ["CD copiado"]
    assert len(discos[0].tracks) == 1


def test_extensao_em_maiuscula_e_aceita(tmp_path, make_track):
    make_track(tmp_path / "d", "01.MP3")
    make_track(tmp_path / "d", "02.WAV")
    assert len(scan(tmp_path)[0].tracks) == 2


def test_todos_os_formatos_aceitos(tmp_path, make_track):
    for nome in ("1.mp3", "2.flac", "3.ogg", "4.oga", "5.m4a", "6.wav"):
        pasta = tmp_path / "d"
        pasta.mkdir(exist_ok=True)
        (pasta / nome).write_bytes(b"")   # vazios: só conferimos a extensão
    assert len(scan(tmp_path)[0].tracks) == 6


def test_arquivos_e_pastas_escondidos_sao_ignorados(tmp_path, make_track):
    make_track(tmp_path / "d", "01.mp3")
    make_track(tmp_path / "d", "._01.mp3")        # lixo que outros sistemas deixam
    make_track(tmp_path / ".thumbnails", "01.mp3")
    discos = scan(tmp_path)
    assert [d.title for d in discos] == ["d"]
    assert len(discos[0].tracks) == 1


def test_pasta_inexistente_devolve_lista_vazia(tmp_path):
    assert scan(tmp_path / "nao-existe") == []


def test_pasta_vazia_devolve_lista_vazia(tmp_path):
    assert scan(tmp_path) == []


# ---------------------------------------------------------------------------
# Varredura: ordem das faixas e da estante
# ---------------------------------------------------------------------------

def test_faixas_ordenadas_pelo_numero(tmp_path, make_track):
    make_track(tmp_path / "d", "a.mp3", title="C", tracknumber="3")
    make_track(tmp_path / "d", "b.mp3", title="A", tracknumber="1")
    make_track(tmp_path / "d", "c.mp3", title="B", tracknumber="2")
    assert [t.title for t in scan(tmp_path)[0].tracks] == ["A", "B", "C"]


def test_faixas_sem_numero_em_ordem_natural_do_nome(tmp_path, make_track):
    for nome in ("Faixa 10.mp3", "Faixa 2.mp3", "Faixa 1.mp3"):
        make_track(tmp_path / "d", nome)
    assert [t.title for t in scan(tmp_path)[0].tracks] == ["Faixa 1", "Faixa 2", "Faixa 10"]


def test_estante_em_ordem_de_artista_e_album(tmp_path, make_track):
    make_track(tmp_path / "p1", "a.mp3", artist="Zeca", album="Vol 2", albumartist="Zeca")
    make_track(tmp_path / "p2", "a.mp3", artist="Zeca", album="Vol 1", albumartist="Zeca")
    make_track(tmp_path / "p3", "a.mp3", artist="Álvaro", album="Único", albumartist="Álvaro")
    assert [d.title for d in scan(tmp_path)] == ["Único", "Vol 1", "Vol 2"]


# ---------------------------------------------------------------------------
# Varredura: artista do disco
# ---------------------------------------------------------------------------

def test_artista_do_album_pela_tag(tmp_path, make_track):
    make_track(tmp_path / "d", "a.mp3", artist="Convidado", albumartist="Zeca")
    make_track(tmp_path / "d", "b.mp3", artist="Zeca", albumartist="Zeca")
    assert scan(tmp_path)[0].artist == "Zeca"


def test_sem_tag_de_album_vale_o_artista_das_faixas(tmp_path, make_track):
    make_track(tmp_path / "d", "a.mp3", artist="Zeca")
    make_track(tmp_path / "d", "b.mp3", artist="zeca")   # caixa diferente, mesmo artista
    assert scan(tmp_path)[0].artist.lower() == "zeca"


def test_convidado_em_uma_faixa_nao_vira_coletanea(tmp_path, make_track):
    for i in range(4):
        make_track(tmp_path / "d", f"{i}.mp3", artist="Zeca")
    make_track(tmp_path / "d", "5.mp3", artist="Zeca e Beto")
    assert scan(tmp_path)[0].artist == "Zeca"


def test_artistas_diferentes_viram_varios_artistas(tmp_path, make_track):
    for i, artista in enumerate(["Ana", "Beto", "Caio", "Dora"]):
        make_track(tmp_path / "d", f"{i}.mp3", artist=artista)
    assert scan(tmp_path)[0].artist == VARIOS_ARTISTAS


@pytest.mark.parametrize("escrita", ["Various Artists", "Vários Artistas", "VA", "Diversos"])
def test_formas_de_escrever_coletanea_viram_varios_artistas(tmp_path, make_track, escrita):
    make_track(tmp_path / "d", "a.mp3", albumartist=escrita)
    assert scan(tmp_path)[0].artist == VARIOS_ARTISTAS


def test_sem_nenhuma_tag_de_artista_o_artista_e_none(tmp_path, make_track):
    make_track(tmp_path / "Boleros", "a.mp3")
    assert scan(tmp_path)[0].artist is None


# ---------------------------------------------------------------------------
# Duplicadas e leitor trocável
# ---------------------------------------------------------------------------

def test_mesma_musica_em_dois_cds_aparece_nos_dois(tmp_path, make_track):
    make_track(tmp_path / "CD1", "01.mp3", title="Samba da Esquina")
    make_track(tmp_path / "CD2", "05.mp3", title="Samba da Esquina")
    discos = scan(tmp_path)
    assert len(discos) == 2
    assert all(len(d.tracks) == 1 and d.tracks[0].title == "Samba da Esquina" for d in discos)
    assert discos[0].tracks[0] != discos[1].tracks[0]   # caminhos diferentes


def test_leitor_de_faixas_pode_ser_trocado(tmp_path, make_track):
    make_track(tmp_path / "d", "01.mp3", title="Real")
    lidos = []

    def leitor_falso(caminho):
        lidos.append(caminho.name)
        return read_track(caminho)

    scan(tmp_path, read=leitor_falso)
    assert lidos == ["01.mp3"]


# -- ano do disco (ADR-0027) ---------------------------------------------------------------

@pytest.mark.parametrize("tag,esperado", [("2005", 2005), ("2005-03-01", 2005), ("1987-1989", 1987)])
def test_o_ano_vem_da_tag_de_data_em_varios_formatos(make_track, tmp_path, tag, esperado):
    caminho = make_track(tmp_path / "CD", "01.mp3", title="A", date=tag)
    assert read_track(caminho).year == esperado


@pytest.mark.parametrize("tag", ["0000", "abcd", "12", "3000", ""])
def test_ano_invalido_ou_ausente_vira_none(make_track, tmp_path, tag):
    tags = {"title": "A"} | ({"date": tag} if tag else {})
    assert read_track(make_track(tmp_path / "CD", "01.mp3", **tags)).year is None


def test_o_ano_tambem_e_lido_de_flac(make_track, tmp_path):
    assert read_track(make_track(tmp_path / "CD", "01.flac", title="A", date="1975")).year == 1975


def test_o_disco_tem_o_ano_que_mais_se_repete_entre_as_faixas(make_track, tmp_path):
    pasta = tmp_path / "musica" / "CD"
    for i, ano in enumerate(("1990", "1990", "1991"), start=1):
        make_track(pasta, f"{i:02d}.mp3", title=f"M{i}", album="CD", date=ano)
    assert scan(tmp_path / "musica")[0].year == 1990


def test_disco_sem_ano_nas_tags_fica_com_year_none(make_track, tmp_path):
    make_track(tmp_path / "musica" / "CD", "01.mp3", title="A", album="CD")
    assert scan(tmp_path / "musica")[0].year is None
