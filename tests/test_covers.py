"""Testes das capas (M1, parte 3)."""

import base64
import os
from pathlib import Path

import mutagen
import pytest
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC
from mutagen.mp3 import MP3

import gi
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf  # noqa: E402

from estante.core.covers import (
    PALETA,
    CoverSource,
    contrast_ratio,
    extract_embedded,
    find_cover,
    make_thumbnail,
    read_image_bytes,
    substitute_cover,
)
from estante.core.library import scan
from estante.core.models import Album


# ---------------------------------------------------------------------------
# Auxiliares: gravar capas embutidas nos três formatos que sabemos gerar
# ---------------------------------------------------------------------------

def embutir(arquivo: Path, imagem: Path) -> bytes:
    """Grava `imagem` como capa dentro do arquivo de áudio. Devolve os bytes."""
    dados = imagem.read_bytes()
    mime = "image/jpeg" if imagem.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    extensao = arquivo.suffix.lower()
    if extensao == ".mp3":
        audio = MP3(arquivo)
        if audio.tags is None:
            audio.add_tags()
        audio.tags.add(APIC(encoding=3, mime=mime, type=3, desc="Capa", data=dados))
        audio.save()
    elif extensao == ".flac":
        figura = Picture()
        figura.data, figura.type, figura.mime = dados, 3, mime
        audio = FLAC(arquivo)
        audio.add_picture(figura)
        audio.save()
    elif extensao == ".ogg":
        figura = Picture()
        figura.data, figura.type, figura.mime = dados, 3, mime
        audio = mutagen.File(arquivo)
        audio["metadata_block_picture"] = [base64.b64encode(figura.write()).decode()]
        audio.save()
    else:
        raise ValueError(extensao)
    return dados


def disco(pasta: Path) -> Album:
    """Monta o disco da pasta com o leitor de verdade."""
    return scan(pasta.parent)[0]


# ---------------------------------------------------------------------------
# Capa embutida
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("extensao", [".mp3", ".flac", ".ogg"])
def test_extrai_a_capa_embutida(tmp_path, make_track, make_image, extensao):
    musica = make_track(tmp_path / "d", f"01{extensao}")
    esperado = embutir(musica, make_image(tmp_path / "capa.jpg"))
    assert extract_embedded(musica) == esperado


def test_sem_capa_embutida_devolve_none(tmp_path, make_track):
    assert extract_embedded(make_track(tmp_path / "d", "01.mp3")) is None


def test_arquivo_corrompido_nao_quebra_a_busca_da_capa(tmp_path):
    ruim = tmp_path / "d" / "01.mp3"
    ruim.parent.mkdir()
    ruim.write_bytes(b"nao e um mp3")
    assert extract_embedded(ruim) is None


def test_prefere_a_capa_frontal_quando_ha_varias(tmp_path, make_track, make_image):
    musica = make_track(tmp_path / "d", "01.mp3")
    contracapa = make_image(tmp_path / "contra.png", 10, 10).read_bytes()
    frente = make_image(tmp_path / "frente.jpg", 20, 20).read_bytes()
    audio = MP3(musica)
    audio.add_tags()
    audio.tags.add(APIC(encoding=3, mime="image/png", type=4, desc="Contracapa", data=contracapa))
    audio.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Frente", data=frente))
    audio.save()
    assert extract_embedded(musica) == frente


# ---------------------------------------------------------------------------
# Onde procurar a capa
# ---------------------------------------------------------------------------

def test_a_capa_embutida_vence_a_imagem_da_pasta(tmp_path, make_track, make_image):
    musica = make_track(tmp_path / "d", "01.mp3")
    embutir(musica, make_image(tmp_path / "embutida.jpg"))
    make_image(tmp_path / "d" / "folder.jpg")
    fonte = find_cover(disco(tmp_path / "d"))
    assert fonte == CoverSource("embedded", musica)


def test_sem_capa_embutida_usa_a_imagem_da_pasta(tmp_path, make_track, make_image):
    make_track(tmp_path / "d", "01.mp3")
    imagem = make_image(tmp_path / "d" / "cover.jpg")
    assert find_cover(disco(tmp_path / "d")) == CoverSource("file", imagem)


@pytest.mark.parametrize("nome", ["folder.jpg", "cover.jpg", "front.jpg", "folder.png",
                                  "cover.png", "front.png", "cover.jpeg"])
def test_nomes_de_imagem_aceitos(tmp_path, make_track, make_image, nome):
    make_track(tmp_path / "d", "01.mp3")
    imagem = make_image(tmp_path / "d" / nome)
    assert find_cover(disco(tmp_path / "d")).path == imagem


def test_nome_da_imagem_ignora_maiusculas(tmp_path, make_track, make_image):
    make_track(tmp_path / "d", "01.mp3")
    imagem = make_image(tmp_path / "d" / "Folder.JPG")
    assert find_cover(disco(tmp_path / "d")).path == imagem


def test_ordem_entre_as_imagens_da_pasta(tmp_path, make_track, make_image):
    make_track(tmp_path / "d", "01.mp3")
    make_image(tmp_path / "d" / "front.jpg")
    make_image(tmp_path / "d" / "cover.jpg")
    escolhida = make_image(tmp_path / "d" / "folder.jpg")
    assert find_cover(disco(tmp_path / "d")).path == escolhida


def test_outras_imagens_da_pasta_nao_servem_de_capa(tmp_path, make_track, make_image):
    make_track(tmp_path / "d", "01.mp3")
    make_image(tmp_path / "d" / "foto_da_festa.jpg")
    assert find_cover(disco(tmp_path / "d")) is None


def test_sem_nenhuma_capa_devolve_none(tmp_path, make_track):
    make_track(tmp_path / "d", "01.mp3")
    assert find_cover(disco(tmp_path / "d")) is None


def test_capa_embutida_so_na_segunda_faixa_tambem_e_achada(tmp_path, make_track, make_image):
    make_track(tmp_path / "d", "01.mp3")
    segunda = make_track(tmp_path / "d", "02.mp3")
    embutir(segunda, make_image(tmp_path / "c.jpg"))
    assert find_cover(disco(tmp_path / "d")) == CoverSource("embedded", segunda)


def test_le_os_bytes_da_capa_de_arquivo_e_da_embutida(tmp_path, make_track, make_image):
    musica = make_track(tmp_path / "d", "01.flac")
    esperado = embutir(musica, make_image(tmp_path / "c.png"))
    assert read_image_bytes(CoverSource("embedded", musica)) == esperado
    imagem = make_image(tmp_path / "d" / "folder.jpg")
    assert read_image_bytes(CoverSource("file", imagem)) == imagem.read_bytes()


def test_imagem_que_sumiu_devolve_none(tmp_path):
    assert read_image_bytes(CoverSource("file", tmp_path / "nao-existe.jpg")) is None


# ---------------------------------------------------------------------------
# Miniaturas
# ---------------------------------------------------------------------------

def dimensoes(caminho: Path) -> tuple[int, int]:
    imagem = GdkPixbuf.Pixbuf.new_from_file(str(caminho))
    return imagem.get_width(), imagem.get_height()


def test_miniatura_e_reduzida_e_mantem_a_proporcao(tmp_path, make_image):
    grande = make_image(tmp_path / "grande.jpg", 1000, 500)
    mini = make_thumbnail(CoverSource("file", grande), tmp_path / "cache", tamanho=100)
    assert mini is not None and mini.suffix == ".png"
    assert dimensoes(mini) == (100, 50)


def test_miniatura_nunca_amplia(tmp_path, make_image):
    pequena = make_image(tmp_path / "pequena.png", 30, 20)
    mini = make_thumbnail(CoverSource("file", pequena), tmp_path / "cache", tamanho=256)
    assert dimensoes(mini) == (30, 20)


def test_miniatura_e_gerada_uma_vez_so(tmp_path, make_image):
    imagem = make_image(tmp_path / "capa.jpg", 300, 300)
    fonte = CoverSource("file", imagem)
    primeira = make_thumbnail(fonte, tmp_path / "cache", tamanho=100)
    horario = os.stat(primeira).st_mtime_ns
    segunda = make_thumbnail(fonte, tmp_path / "cache", tamanho=100)
    assert segunda == primeira
    assert os.stat(segunda).st_mtime_ns == horario     # não foi reescrita


def test_miniatura_nova_quando_a_imagem_muda(tmp_path, make_image):
    imagem = make_image(tmp_path / "capa.jpg", 300, 300)
    fonte = CoverSource("file", imagem)
    antiga = make_thumbnail(fonte, tmp_path / "cache", tamanho=100)
    make_image(imagem, 400, 400)                        # troca a imagem
    os.utime(imagem, (1, 1))                            # e a data de modificação
    nova = make_thumbnail(fonte, tmp_path / "cache", tamanho=100)
    assert nova != antiga


def test_miniatura_de_capa_embutida(tmp_path, make_track, make_image):
    musica = make_track(tmp_path / "d", "01.flac")
    embutir(musica, make_image(tmp_path / "c.jpg", 500, 500))
    mini = make_thumbnail(CoverSource("embedded", musica), tmp_path / "cache", tamanho=64)
    assert dimensoes(mini) == (64, 64)


def test_imagem_ilegivel_devolve_none_sem_quebrar(tmp_path):
    ruim = tmp_path / "folder.jpg"
    ruim.write_bytes(b"isto nao e uma imagem")
    assert make_thumbnail(CoverSource("file", ruim), tmp_path / "cache") is None
    assert not (tmp_path / "cache" / "miniaturas").exists() or not list(
        (tmp_path / "cache" / "miniaturas").glob("*.png"))


def test_fonte_inexistente_devolve_none(tmp_path):
    assert make_thumbnail(CoverSource("file", tmp_path / "x.jpg"), tmp_path / "cache") is None


def test_miniatura_nao_deixa_arquivo_temporario(tmp_path, make_image):
    imagem = make_image(tmp_path / "capa.jpg", 300, 300)
    make_thumbnail(CoverSource("file", imagem), tmp_path / "cache", tamanho=100)
    assert not list((tmp_path / "cache").rglob("*.tmp"))


# ---------------------------------------------------------------------------
# Capa substituta
# ---------------------------------------------------------------------------

def disco_chamado(nome: str) -> Album:
    return Album(folder=Path("/m") / nome, title=nome)


@pytest.mark.parametrize("cor", PALETA)
def test_toda_cor_da_paleta_tem_contraste_aaa_com_o_texto(cor):
    assert contrast_ratio("#FFFFFF", cor) >= 7.0


def test_mesmo_disco_sempre_a_mesma_cor():
    a = substitute_cover(disco_chamado("Boleros"))
    b = substitute_cover(disco_chamado("Boleros"))
    assert a == b


def test_cor_nao_depende_de_acento_nem_de_maiuscula():
    assert (substitute_cover(disco_chamado("Seresta Á Noite")).background
            == substitute_cover(disco_chamado("seresta a noite")).background)


def test_a_cor_e_estavel_entre_execucoes():
    # Valores fixos de propósito: provam que não usamos o hash() do Python (que
    # muda a cada execução) e avisam se alguém mudar o algoritmo ou a paleta,
    # o que trocaria a cor de todos os discos do idoso de um dia para o outro.
    assert substitute_cover(disco_chamado("Boleros")).background == "#3B2D6B"
    assert substitute_cover(disco_chamado("Clássicos do Samba")).background == "#1F5A2E"


def test_discos_diferentes_espalham_as_cores():
    nomes = [f"Disco {i}" for i in range(40)]
    cores = {substitute_cover(disco_chamado(n)).background for n in nomes}
    assert len(cores) >= 8        # com 12 cores e 40 nomes, esperamos boa variedade


def test_capa_substituta_escreve_o_nome_do_disco_em_branco():
    capa = substitute_cover(disco_chamado("Clássicos do Samba"))
    assert capa.title == "Clássicos do Samba"
    assert capa.text_color == "#FFFFFF"
    assert capa.background in PALETA
