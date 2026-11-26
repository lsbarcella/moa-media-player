"""Testes da varredura incremental e do cache de capas (M1, parte 4)."""

import os
from pathlib import Path

import pytest

import moa.core.covers as covers
import moa.core.library as library
from moa.core.db import Database
from moa.core.library import refresh_library, scan


@pytest.fixture
def db():
    banco = Database(":memory:")
    yield banco
    banco.close()


@pytest.fixture
def leituras(monkeypatch):
    """Conta quantas vezes um arquivo de áudio foi realmente aberto e lido."""
    lidos = []
    original = library.read_track

    def contador(caminho):
        lidos.append(caminho.name)
        return original(caminho)

    monkeypatch.setattr(library, "read_track", contador)
    return lidos


def mexer(caminho: Path, segundos: int = 100):
    """Muda a data de modificação do arquivo (como se ele tivesse sido alterado)."""
    estado = caminho.stat()
    os.utime(caminho, ns=(estado.st_atime_ns, estado.st_mtime_ns + segundos * 10**9))


@pytest.fixture
def biblioteca(tmp_path, make_track):
    raiz = tmp_path / "musica"
    make_track(raiz / "Boleros", "01.mp3", title="Primeira", tracknumber="1", artist="Ana")
    make_track(raiz / "Boleros", "02.mp3", title="Segunda", tracknumber="2", artist="Ana")
    make_track(raiz / "Valsas", "01.flac", title="Valsa", artist="Beto")
    return raiz


# ---------------------------------------------------------------------------
# Varredura incremental
# ---------------------------------------------------------------------------

def test_o_resultado_e_igual_ao_da_varredura_normal(biblioteca, db):
    assert refresh_library(biblioteca, db) == scan(biblioteca)


def test_segunda_abertura_nao_le_nenhum_arquivo(biblioteca, db, leituras):
    refresh_library(biblioteca, db)
    assert len(leituras) == 3
    leituras.clear()
    refresh_library(biblioteca, db)
    assert leituras == []                 # tudo veio do cache


def test_resultado_do_cache_e_igual_ao_da_primeira_leitura(biblioteca, db):
    primeira = refresh_library(biblioteca, db)
    segunda = refresh_library(biblioteca, db)
    assert segunda == primeira


def test_arquivo_alterado_e_relido_e_so_ele(biblioteca, db, leituras):
    refresh_library(biblioteca, db)
    leituras.clear()
    mexer(biblioteca / "Valsas" / "01.flac")
    refresh_library(biblioteca, db)
    assert leituras == ["01.flac"]


def test_etiqueta_nova_aparece_depois_da_alteracao(biblioteca, db, make_track):
    refresh_library(biblioteca, db)
    make_track(biblioteca / "Valsas", "01.flac", title="Título Novo")   # reescreve o arquivo
    mexer(biblioteca / "Valsas" / "01.flac")
    disco = [d for d in refresh_library(biblioteca, db) if d.title == "Valsas"][0]
    assert disco.tracks[0].title == "Título Novo"


def test_arquivo_novo_e_pego(biblioteca, db, make_track, leituras):
    refresh_library(biblioteca, db)
    leituras.clear()
    make_track(biblioteca / "Boleros", "03.mp3", title="Terceira", tracknumber="3")
    discos = refresh_library(biblioteca, db)
    assert leituras == ["03.mp3"]
    assert [t.title for t in [d for d in discos if d.title == "Boleros"][0].tracks][-1] == "Terceira"


def test_arquivo_apagado_some_do_resultado_e_do_cache(biblioteca, db):
    refresh_library(biblioteca, db)
    (biblioteca / "Boleros" / "02.mp3").unlink()
    discos = refresh_library(biblioteca, db)
    assert len([t for d in discos for t in d.tracks]) == 2
    assert str(biblioteca / "Boleros" / "02.mp3") not in db.load_tracks()


def test_pasta_inteira_apagada_some_da_estante(biblioteca, db):
    refresh_library(biblioteca, db)
    for arquivo in (biblioteca / "Valsas").iterdir():
        arquivo.unlink()
    (biblioteca / "Valsas").rmdir()
    assert [d.title for d in refresh_library(biblioteca, db)] == ["Boleros"]


def test_pasta_de_musica_inexistente_nao_quebra(tmp_path, db):
    assert refresh_library(tmp_path / "nao-existe", db) == []


def test_recupera_se_o_banco_foi_apagado(biblioteca, tmp_path, leituras):
    caminho = tmp_path / "moa.db"
    primeiro = Database.open(caminho)
    refresh_library(biblioteca, primeiro)
    primeiro.close()
    caminho.unlink()                       # o cache sumiu
    leituras.clear()
    segundo = Database.open(caminho)
    discos = refresh_library(biblioteca, segundo)
    segundo.close()
    assert len(leituras) == 3              # releu tudo e seguiu em frente
    assert len(discos) == 2


# ---------------------------------------------------------------------------
# Cache de capas
# ---------------------------------------------------------------------------

@pytest.fixture
def chamadas(monkeypatch):
    """Conta as buscas de capa e as gerações de miniatura de verdade."""
    contagem = {"find": 0, "thumb": 0}
    achar, miniatura = covers.find_cover, covers.make_thumbnail

    def achar_contando(disco):
        contagem["find"] += 1
        return achar(disco)

    def miniatura_contando(*args, **kwargs):
        contagem["thumb"] += 1
        return miniatura(*args, **kwargs)

    monkeypatch.setattr(covers, "find_cover", achar_contando)
    monkeypatch.setattr(covers, "make_thumbnail", miniatura_contando)
    return contagem


@pytest.fixture
def discos_com_capa(biblioteca, make_image):
    make_image(biblioteca / "Boleros" / "folder.jpg", 600, 600)    # Valsas fica sem capa


def atualizar(biblioteca, db, cache):
    discos = refresh_library(biblioteca, db)
    return discos, covers.refresh_covers(discos, db, cache, tamanho=100)


def test_disco_com_capa_ganha_miniatura_e_disco_sem_capa_fica_com_none(
        biblioteca, discos_com_capa, db, tmp_path):
    discos, mini = atualizar(biblioteca, db, tmp_path / "cache")
    por_titulo = {d.title: mini[d.id] for d in discos}
    assert por_titulo["Boleros"].exists() and por_titulo["Boleros"].suffix == ".png"
    assert por_titulo["Valsas"] is None


def test_segunda_abertura_nao_procura_nem_gera_nada(
        biblioteca, discos_com_capa, db, tmp_path, chamadas):
    atualizar(biblioteca, db, tmp_path / "cache")
    assert chamadas == {"find": 2, "thumb": 1}
    chamadas.update(find=0, thumb=0)
    atualizar(biblioteca, db, tmp_path / "cache")
    assert chamadas == {"find": 0, "thumb": 0}        # tudo veio do banco


def test_resultado_e_o_mesmo_nas_duas_aberturas(biblioteca, discos_com_capa, db, tmp_path):
    _, primeira = atualizar(biblioteca, db, tmp_path / "cache")
    _, segunda = atualizar(biblioteca, db, tmp_path / "cache")
    assert segunda == primeira


def test_capa_nova_na_pasta_e_notada(biblioteca, discos_com_capa, db, tmp_path, make_image):
    discos, antes = atualizar(biblioteca, db, tmp_path / "cache")
    valsas = [d for d in discos if d.title == "Valsas"][0]
    assert antes[valsas.id] is None
    # coloca um folder.jpg no disco que não tinha; a data da pasta muda sozinha
    pasta = biblioteca / "Valsas"
    os.utime(pasta, ns=(1, 1))                         # garante uma data de pasta diferente da futura
    atualizar(biblioteca, db, tmp_path / "cache")      # registra a data velha
    make_image(pasta / "folder.jpg", 300, 300)
    discos, depois = atualizar(biblioteca, db, tmp_path / "cache")
    valsas = [d for d in discos if d.title == "Valsas"][0]
    assert depois[valsas.id] is not None


def test_miniatura_apagada_do_cache_e_refeita_sem_procurar_a_capa(
        biblioteca, discos_com_capa, db, tmp_path, chamadas):
    discos, mini = atualizar(biblioteca, db, tmp_path / "cache")
    boleros = [d for d in discos if d.title == "Boleros"][0]
    mini[boleros.id].unlink()                          # alguém limpou o cache
    chamadas.update(find=0, thumb=0)
    _, de_novo = atualizar(biblioteca, db, tmp_path / "cache")
    assert de_novo[boleros.id].exists()
    assert chamadas == {"find": 0, "thumb": 1}


def test_imagem_trocada_gera_miniatura_nova_e_apaga_a_velha(
        biblioteca, discos_com_capa, db, tmp_path, make_image):
    discos, antes = atualizar(biblioteca, db, tmp_path / "cache")
    boleros = [d for d in discos if d.title == "Boleros"][0]
    velha = antes[boleros.id]
    imagem = biblioteca / "Boleros" / "folder.jpg"
    make_image(imagem, 800, 800)
    mexer(imagem)
    mexer(biblioteca / "Boleros")                      # a pasta também registra a mudança
    _, depois = atualizar(biblioteca, db, tmp_path / "cache")
    assert depois[boleros.id] != velha
    assert not velha.exists()                          # miniatura órfã removida
    assert len(list((tmp_path / "cache" / "miniaturas").glob("*.png"))) == 1


def test_disco_apagado_perde_a_miniatura_e_o_registro(
        biblioteca, discos_com_capa, db, tmp_path):
    discos, mini = atualizar(biblioteca, db, tmp_path / "cache")
    boleros = [d for d in discos if d.title == "Boleros"][0]
    for arquivo in (biblioteca / "Boleros").iterdir():
        arquivo.unlink()
    (biblioteca / "Boleros").rmdir()
    atualizar(biblioteca, db, tmp_path / "cache")
    assert db.get_cover(boleros.id) is None
    assert not mini[boleros.id].exists()


def test_imagem_ilegivel_nao_e_tentada_de_novo_a_cada_abertura(
        biblioteca, db, tmp_path, chamadas):
    (biblioteca / "Boleros" / "folder.jpg").write_bytes(b"isto nao e uma imagem")
    discos, mini = atualizar(biblioteca, db, tmp_path / "cache")
    boleros = [d for d in discos if d.title == "Boleros"][0]
    assert mini[boleros.id] is None                    # cai na capa substituta
    chamadas.update(find=0, thumb=0)
    atualizar(biblioteca, db, tmp_path / "cache")
    assert chamadas == {"find": 0, "thumb": 0}         # não insiste
