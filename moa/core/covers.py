# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Capas dos discos: a embutida, a imagem da pasta ou uma capa substituta.

Ordem de preferência (CLAUDE.md, seção 8):
1. a capa embutida nas faixas;
2. `folder.jpg`, `cover.jpg` ou `front.jpg` (também `.png`) na pasta do disco;
3. uma capa substituta: o nome do disco em letras grandes sobre uma cor sólida,
   sempre a mesma cor para o mesmo nome.

Duas ideias de desempenho guiam este módulo (a meta é a estante abrir em até
3 s num notebook antigo com HD mecânico):

- Achar a capa exige abrir arquivos de áudio. Por isso `find_cover` é CARA e
  quem chama deve guardar o resultado no cache (parte 4 do M1) em vez de
  repetir a busca a cada abertura.
- Decodificar um JPEG grande a cada abertura também é caro. Por isso
  `make_thumbnail` reduz a imagem UMA vez e guarda a miniatura em disco.

A capa substituta é só dado (texto e cores). Quem desenha é a interface, com
o CSS do GTK. Assim este módulo continua sem GTK.
"""

import base64
import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import mutagen
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4Tags

from moa.core.models import Album
from moa.core.textutil import fold

if TYPE_CHECKING:       # só para o editor entender o tipo; evita importação circular
    from moa.core.db import Database

log = logging.getLogger(__name__)

# Nomes de imagem procurados na pasta, em ordem de preferência. A comparação
# ignora maiúsculas (o Windows costuma gravar "Folder.jpg").
_NOMES = ("folder", "cover", "front")
_EXTENSOES = (".jpg", ".jpeg", ".png")

# Quantas faixas olhamos atrás de uma capa embutida. Quem etiqueta com o
# Picard embute a capa em todas, então não vale abrir o disco inteiro.
_FAIXAS_VERIFICADAS = 3


# ---------------------------------------------------------------------------
# Onde está a capa
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CoverSource:
    """De onde vem a imagem da capa.

    kind == "embedded": está dentro do arquivo de áudio `path`.
    kind == "file":     `path` é um arquivo de imagem na pasta do disco.
    """

    kind: str
    path: Path


def _escolher_imagem(figuras) -> bytes | None:
    """Entre várias figuras embutidas, prefere a "capa frontal" (tipo 3)."""
    figuras = [f for f in figuras if f is not None]
    if not figuras:
        return None
    for figura in figuras:
        if getattr(figura, "type", None) == 3:
            return figura.data
    return figuras[0].data


def extract_embedded(path: Path) -> bytes | None:
    """Extrai os bytes da capa embutida num arquivo de áudio, ou None.

    Cada formato guarda a capa de um jeito: ID3 (mp3), bloco de figura (flac),
    átomo `covr` (m4a) e comentário codificado em base64 (ogg).
    """
    try:
        arquivo = mutagen.File(path)
    except Exception as erro:  # o mutagen pode levantar vários tipos de erro
        log.warning("não consegui abrir %s para procurar a capa: %s", path, erro)
        return None
    if arquivo is None:
        return None

    try:
        if isinstance(arquivo, FLAC):
            return _escolher_imagem(arquivo.pictures)

        tags = arquivo.tags
        if tags is None:
            return None

        if hasattr(tags, "getall"):                      # ID3 (mp3, wav)
            return _escolher_imagem(tags.getall("APIC"))

        if isinstance(tags, MP4Tags):                    # m4a
            capas = tags.get("covr")
            return bytes(capas[0]) if capas else None

        if "metadata_block_picture" in tags:             # ogg
            figuras = [Picture(base64.b64decode(b)) for b in tags["metadata_block_picture"]]
            return _escolher_imagem(figuras)
    except Exception as erro:
        log.warning("capa embutida ilegível em %s: %s", path, erro)
    return None


def find_cover(album: Album) -> CoverSource | None:
    """Procura a capa do disco: embutida primeiro, depois a imagem da pasta.

    Devolve None quando não há nenhuma (a interface usa a capa substituta).
    ATENÇÃO: abre arquivos de áudio. Guarde o resultado no cache.
    """
    for faixa in album.tracks[:_FAIXAS_VERIFICADAS]:
        if extract_embedded(faixa.path) is not None:
            return CoverSource("embedded", faixa.path)

    try:
        arquivos = {e.name.lower(): Path(e.path) for e in os.scandir(album.folder) if e.is_file()}
    except OSError as erro:
        log.warning("não consegui listar a pasta %s: %s", album.folder, erro)
        return None
    for nome in _NOMES:
        for extensao in _EXTENSOES:
            achado = arquivos.get(nome + extensao)
            if achado is not None:
                return CoverSource("file", achado)
    return None


def read_image_bytes(fonte: CoverSource) -> bytes | None:
    """Lê os bytes da imagem de uma capa, de onde ela estiver."""
    if fonte.kind == "embedded":
        return extract_embedded(fonte.path)
    try:
        return fonte.path.read_bytes()
    except OSError as erro:
        log.warning("não consegui ler a imagem %s: %s", fonte.path, erro)
        return None


# ---------------------------------------------------------------------------
# Miniaturas
# ---------------------------------------------------------------------------

def _caminho_da_miniatura(fonte: CoverSource, pasta_cache: Path, tamanho: int) -> Path:
    """Nome da miniatura. Muda quando a imagem de origem muda (data e tamanho)."""
    try:
        estado = fonte.path.stat()
        assinatura = f"{estado.st_mtime_ns}|{estado.st_size}"
    except OSError:
        assinatura = "?"
    chave = f"{fonte.kind}|{fonte.path}|{assinatura}|{tamanho}"
    return pasta_cache / "miniaturas" / (hashlib.sha1(chave.encode()).hexdigest() + ".png")


def make_thumbnail(fonte: CoverSource, pasta_cache: Path, tamanho: int = 256) -> Path | None:
    """Gera (uma vez) a miniatura da capa e devolve o caminho dela.

    A imagem é reduzida para caber em `tamanho` x `tamanho`, mantendo a
    proporção, e nunca é ampliada. Se a miniatura já existe, só devolve o
    caminho. Imagem ilegível devolve None, sem erro (a interface cai na capa
    substituta).
    """
    destino = _caminho_da_miniatura(fonte, Path(pasta_cache), tamanho)
    if destino.exists():
        return destino

    dados = read_image_bytes(fonte)
    if not dados:
        return None

    # Importado aqui para este módulo carregar mesmo sem o GdkPixbuf. O
    # GdkPixbuf não é o GTK: é só a biblioteca que decodifica imagens.
    import gi
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import GdkPixbuf, GLib

    def ajustar(carregador, largura, altura):
        # Chamado assim que o tamanho da imagem é conhecido: pede ao decodificador
        # que já entregue a imagem reduzida (muito mais barato para JPEG grande).
        maior = max(largura, altura)
        if maior > tamanho:
            fator = tamanho / maior
            carregador.set_size(max(1, round(largura * fator)), max(1, round(altura * fator)))

    carregador = GdkPixbuf.PixbufLoader()
    carregador.connect("size-prepared", ajustar)
    try:
        carregador.write(dados)
        carregador.close()
        imagem = carregador.get_pixbuf()
    except GLib.Error as erro:
        log.warning("imagem de capa ilegível (%s): %s", fonte.path, erro)
        try:
            carregador.close()
        except GLib.Error:
            pass
        return None
    if imagem is None:
        return None

    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(".tmp")
    try:
        imagem.savev(str(temporario), "png", [], [])
        os.replace(temporario, destino)     # troca atômica: nunca fica meio arquivo
    except (GLib.Error, OSError) as erro:
        log.warning("não consegui gravar a miniatura %s: %s", destino, erro)
        return None
    return destino


def _assinatura_do_disco(disco: Album) -> str:
    """Resumo que muda quando o disco muda, para saber se o cache da capa vale.

    Entram a data da pasta (muda quando um arquivo é criado ou apagado nela,
    por exemplo um `folder.jpg` novo) e o caminho, a data e o tamanho de cada
    faixa (muda quando uma música é trocada ou re-etiquetada).
    """
    resumo = hashlib.sha1()
    try:
        resumo.update(str(os.stat(disco.folder).st_mtime_ns).encode())
    except OSError:
        pass
    for faixa in disco.tracks:
        resumo.update(f"|{faixa.path}|{faixa.mtime}|{faixa.size}".encode())
    return resumo.hexdigest()


def refresh_covers(discos: list[Album], db: "Database", pasta_cache: Path,
                   tamanho: int = 256) -> dict[str, Path | None]:
    """Devolve a miniatura de cada disco (pelo `album.id`), usando o cache.

    Um disco que não mudou desde a última vez NÃO é reaberto: a decisão e a
    miniatura vêm do banco. Só os discos novos ou alterados passam por
    `find_cover` e `make_thumbnail`. O valor None significa "sem miniatura":
    a interface desenha a capa substituta.

    Miniaturas que ninguém mais usa (disco apagado, imagem trocada) são
    removidas do cache.
    """
    pasta_cache = Path(pasta_cache)
    resultado: dict[str, Path | None] = {}

    for disco in discos:
        assinatura = _assinatura_do_disco(disco)
        registro = db.get_cover(disco.id)

        if registro is not None and registro.signature == assinatura:
            fonte = registro.source
            miniatura = registro.thumbnail
            if fonte is not None and miniatura is not None and not miniatura.exists():
                # Alguém limpou o cache de miniaturas: refaz sem procurar a fonte de novo.
                miniatura = make_thumbnail(fonte, pasta_cache, tamanho)
                db.save_cover(disco.id, assinatura, fonte, miniatura)
        else:
            fonte = find_cover(disco)
            miniatura = make_thumbnail(fonte, pasta_cache, tamanho) if fonte else None
            db.save_cover(disco.id, assinatura, fonte, miniatura)
        resultado[disco.id] = miniatura

    db.delete_covers_except(d.id for d in discos)
    _limpar_miniaturas_orfas(pasta_cache, {m for m in resultado.values() if m is not None})
    return resultado


def _limpar_miniaturas_orfas(pasta_cache: Path, em_uso: set[Path]) -> None:
    """Apaga do cache as miniaturas (e temporários) que nenhum disco usa."""
    pasta = pasta_cache / "miniaturas"
    if not pasta.is_dir():
        return
    for arquivo in pasta.iterdir():
        if arquivo.suffix in (".png", ".tmp") and arquivo not in em_uso:
            try:
                arquivo.unlink()
            except OSError as erro:
                log.warning("não consegui apagar a miniatura velha %s: %s", arquivo, erro)


# ---------------------------------------------------------------------------
# Capa substituta
# ---------------------------------------------------------------------------

# Cores escuras, todas com contraste de pelo menos 7:1 contra o branco
# (WCAG nível AAA). Os testes conferem isso.
PALETA = (
    "#8A2D12", "#1F4D6B", "#6B1F4D", "#1F5A2E", "#5A3A12", "#7A3B00",
    "#3B2D6B", "#4A5A12", "#12486B", "#6B2D2D", "#2D3B3B", "#7A1F2E",
)
COR_DO_TEXTO = "#FFFFFF"


@dataclass(frozen=True)
class SubstituteCover:
    """O que a interface precisa para desenhar a capa substituta."""

    title: str         # nome do disco, para escrever em letras grandes
    background: str    # cor sólida de fundo, como "#8A2D12"
    text_color: str    # cor do texto, com contraste de 7:1 ou mais sobre o fundo


def substitute_cover(album: Album) -> SubstituteCover:
    """Capa substituta: o nome do disco sobre uma cor derivada do nome.

    A cor é sempre a mesma para o mesmo nome, em qualquer máquina e em
    qualquer abertura. Por isso usamos o SHA-1 do nome: o `hash()` do Python
    muda a cada execução e não serviria. Maiúsculas e acentos não mudam a cor.
    """
    resumo = hashlib.sha1(fold(album.title).encode("utf-8")).digest()
    cor = PALETA[int.from_bytes(resumo[:4], "big") % len(PALETA)]
    return SubstituteCover(title=album.title, background=cor, text_color=COR_DO_TEXTO)


def contrast_ratio(cor_a: str, cor_b: str) -> float:
    """Razão de contraste da WCAG entre duas cores "#RRGGBB" (de 1 a 21)."""

    def luminancia(cor: str) -> float:
        canais = [int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    claro, escuro = sorted((luminancia(cor_a), luminancia(cor_b)), reverse=True)
    return (claro + 0.05) / (escuro + 0.05)
