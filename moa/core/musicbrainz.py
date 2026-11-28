# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Atualização opcional e oportunista de nomes e capas pelo MusicBrainz (ADR-0003). Sem GTK.

Regras que este arquivo cumpre (CLAUDE.md, seção 9, "Rede opcional"):

- **Tocar e navegar nunca dependem da rede.** Nada aqui é chamado para tocar música.
  O app só usa este módulo numa thread de segundo plano, depois que a estante já está na tela.
- **Falha silenciosa.** Sem internet, tempo esgotado, servidor fora do ar ou resposta estranha:
  só vai para o log. O idoso não percebe nada.
- **Na dúvida, não muda nada.** Com o ID do MusicBrainz nas tags a consulta é exata. Sem ele,
  só se aceita um disco com o MESMO nome, o MESMO artista e o MESMO número de faixas.
- **Nada é reescrito nos arquivos de música.** O resultado fica numa tabela do banco do app e
  é aplicado POR CIMA das tags, só na próxima abertura (a estante não muda enquanto o idoso olha).
- **No máximo 1 requisição por segundo**, como o MusicBrainz pede.
- **Privacidade.** Só vai pela rede o ID do álbum, ou o artista e o nome do álbum. O cabeçalho
  de identificação é genérico: sem e-mail, sem nome de pessoa, sem dados da máquina.

Só usa o `urllib` do Python (nenhuma dependência nova).
"""

import json
import logging
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import replace
from pathlib import Path
from typing import Callable

from moa.core.db import Database, RegistroMB
from moa.core.library import read_musicbrainz_album_id, title_from_filename
from moa.core.models import Album

log = logging.getLogger(__name__)

USER_AGENT = "MoaMediaPlayer/0.1"
URL_DO_MUSICBRAINZ = "https://musicbrainz.org/ws/2"
URL_DAS_CAPAS = "https://coverartarchive.org"

INTERVALO_ENTRE_PEDIDOS = 1.0            # segundos (limite do MusicBrainz)
TEMPO_LIMITE = 10.0                      # segundos por pedido
TAMANHO_MAXIMO_JSON = 2 * 1024 * 1024
TAMANHO_MAXIMO_CAPA = 6 * 1024 * 1024
TENTAR_DE_NOVO_APOS = 30 * 24 * 3600     # um disco "sem certeza" é reconsultado depois de 30 dias
FALHAS_SEGUIDAS_PARA_DESISTIR = 3        # provavelmente sem rede: para e tenta na próxima abertura

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


class ErroDeRede(Exception):
    """Qualquer problema de rede ou de resposta. Nunca chega ao idoso: vai para o log."""


# ---------------------------------------------------------------------------
# Cliente HTTP
# ---------------------------------------------------------------------------

class Limitador:
    """Garante um intervalo mínimo entre pedidos (1 por segundo)."""

    def __init__(self, intervalo: float = INTERVALO_ENTRE_PEDIDOS,
                 relogio: Callable[[], float] = time.monotonic,
                 dormir: Callable[[float], None] = time.sleep):
        self._intervalo = intervalo
        self._relogio = relogio
        self._dormir = dormir
        self._ultimo: float | None = None

    def esperar(self) -> None:
        agora = self._relogio()
        if self._ultimo is not None:
            falta = self._intervalo - (agora - self._ultimo)
            if falta > 0:
                self._dormir(falta)
                agora = self._relogio()
        self._ultimo = agora


class Cliente:
    """Faz os pedidos ao MusicBrainz e ao Cover Art Archive. Só levanta `ErroDeRede`."""

    def __init__(self, url_mb: str = URL_DO_MUSICBRAINZ, url_capas: str = URL_DAS_CAPAS,
                 limitador: Limitador | None = None, tempo_limite: float = TEMPO_LIMITE):
        self._url_mb = url_mb.rstrip("/")
        self._url_capas = url_capas.rstrip("/")
        self._limitador = limitador or Limitador()
        self._tempo_limite = tempo_limite

    def _pedir(self, url: str, limite: int, aceita: str) -> bytes | None:
        """Devolve os bytes, ou None se o servidor disse "não existe" (404)."""
        self._limitador.esperar()
        pedido = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": aceita})
        try:
            with urllib.request.urlopen(pedido, timeout=self._tempo_limite) as resposta:
                dados = resposta.read(limite + 1)
        except urllib.error.HTTPError as erro:
            if erro.code == 404:
                return None
            raise ErroDeRede(f"o servidor respondeu {erro.code}") from erro
        except (urllib.error.URLError, OSError, ValueError) as erro:
            raise ErroDeRede(f"falha de rede: {erro}") from erro
        if len(dados) > limite:
            raise ErroDeRede("resposta grande demais")
        return dados

    def _json(self, url: str) -> dict | None:
        dados = self._pedir(url, TAMANHO_MAXIMO_JSON, "application/json")
        if dados is None:
            return None
        try:
            resposta = json.loads(dados)
        except ValueError as erro:
            raise ErroDeRede(f"resposta que não é JSON: {erro}") from erro
        if not isinstance(resposta, dict):
            raise ErroDeRede("resposta com formato inesperado")
        return resposta

    def disco_por_id(self, mbid: str) -> dict | None:
        if not _UUID.match(mbid):             # o ID entra na URL: só aceitamos o formato certo
            return None
        return self._json(f"{self._url_mb}/release/{mbid}?inc=recordings+artist-credits&fmt=json")

    def procurar_disco(self, album: str, artista: str) -> list[dict]:
        consulta = f'release:"{_sem_aspas(album)}" AND artist:"{_sem_aspas(artista)}"'
        parametros = urllib.parse.urlencode({"query": consulta, "fmt": "json", "limit": 10})
        resposta = self._json(f"{self._url_mb}/release/?{parametros}") or {}
        achados = resposta.get("releases")
        return [r for r in achados if isinstance(r, dict)] if isinstance(achados, list) else []

    def capa_frontal(self, mbid: str) -> bytes | None:
        if not _UUID.match(mbid):
            return None
        return self._pedir(f"{self._url_capas}/release/{mbid}/front-500", TAMANHO_MAXIMO_CAPA,
                           "image/jpeg, image/png")


def _sem_aspas(texto: str) -> str:
    return texto.replace("\\", " ").replace('"', " ").strip()


# ---------------------------------------------------------------------------
# Entender as respostas
# ---------------------------------------------------------------------------

def _normalizar(texto: str | None) -> str:
    """Para comparar nomes: sem maiúsculas, acentos de caixa e pontuação."""
    return re.sub(r"\W+", "", (texto or "").casefold())


def artista_do_disco(disco: dict) -> str | None:
    """Junta o "artist-credit" ("Tom Jobim" + " & " + "Vinicius") num nome só."""
    partes = []
    for credito in disco.get("artist-credit") or []:
        if not isinstance(credito, dict):
            continue
        nome = credito.get("name") or (credito.get("artist") or {}).get("name")
        if nome:
            partes.append(f"{nome}{credito.get('joinphrase') or ''}")
    return "".join(partes).strip() or None


def titulos_das_faixas(disco: dict) -> tuple[str, ...]:
    """Os nomes das faixas, na ordem (todos os CDs do disco, um depois do outro)."""
    nomes = []
    for midia in disco.get("media") or []:
        for faixa in (midia.get("tracks") or []) if isinstance(midia, dict) else []:
            nomes.append(str(faixa.get("title") or "").strip() if isinstance(faixa, dict) else "")
    return tuple(nomes)


def escolher_correspondencia(candidatos: list[dict], album: str, artista: str,
                             total_de_faixas: int) -> str | None:
    """O ID do disco que bate EXATAMENTE em nome, artista e número de faixas; senão None."""
    for candidato in candidatos:
        mbid = candidato.get("id")
        if not isinstance(mbid, str) or not _UUID.match(mbid):
            continue
        if (_normalizar(candidato.get("title")) == _normalizar(album)
                and _normalizar(artista_do_disco(candidato)) == _normalizar(artista)
                and candidato.get("track-count") == total_de_faixas):
            return mbid
    return None


def _formato_da_imagem(dados: bytes) -> str | None:
    if dados.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    return None


# ---------------------------------------------------------------------------
# O trabalho em segundo plano
# ---------------------------------------------------------------------------

class Atualizador:
    """Consulta o MusicBrainz para os discos que ainda podem melhorar e guarda o resultado.

    Roda numa thread. Abre o PRÓPRIO `Database` (uma conexão por thread, como a varredura).
    """

    def __init__(self, caminho_do_banco: Path, pasta_de_capas: Path,
                 esta_online: Callable[[], bool], cliente: Cliente | None = None,
                 agora: Callable[[], float] = time.time):
        self._caminho_do_banco = caminho_do_banco
        self._pasta_de_capas = Path(pasta_de_capas)
        self._esta_online = esta_online
        self._cliente = cliente or Cliente()
        self._agora = agora

    def executar(self, discos: list[Album], miniaturas: dict[str, Path | None]) -> int:
        """Devolve quantos discos foram consultados com sucesso. Nunca levanta erro de rede."""
        if not self._esta_online():
            log.info("musicbrainz: sem conexão, nada a fazer")
            return 0
        banco = Database(self._caminho_do_banco)
        consultados = falhas = 0
        try:
            registros = banco.load_mb()
            for disco in discos:
                if not self._esta_online():
                    break
                precisa_capa = miniaturas.get(disco.id) is None
                if not self._vale_consultar(disco, registros.get(disco.id), precisa_capa):
                    continue
                try:
                    registro = self._consultar(disco, precisa_capa)
                except ErroDeRede as erro:
                    falhas += 1
                    log.info("musicbrainz: %s (%s)", erro, disco.title)
                    if falhas >= FALHAS_SEGUIDAS_PARA_DESISTIR:
                        log.info("musicbrainz: falhas seguidas, tento de novo na próxima abertura")
                        break
                    continue
                except Exception:                  # um disco estranho não pode parar os outros
                    log.exception("musicbrainz: erro inesperado no disco %s", disco.title)
                    continue
                falhas = 0
                banco.save_mb(disco.id, registro)
                consultados += 1
            banco.delete_mb_except(d.id for d in discos)
        finally:
            banco.close()
        return consultados

    def _vale_consultar(self, disco: Album, registro: RegistroMB | None, precisa_capa: bool) -> bool:
        if not disco.tracks:
            return False
        if registro is not None:
            if registro.status == "ok":
                return False
            if self._agora() - registro.checked_at < TENTAR_DE_NOVO_APOS:
                return False
        # Só vale a pena perguntar se algo pode melhorar: o disco sem nome nas tags ou sem capa.
        return precisa_capa or _sem_nome_nas_tags(disco)

    def _consultar(self, disco: Album, precisa_capa: bool) -> RegistroMB:
        agora = self._agora()
        mbid = self._achar_o_id(disco)
        informacao = self._cliente.disco_por_id(mbid) if mbid else None
        if informacao is None:
            return RegistroMB("nada", checked_at=agora)       # na dúvida, não muda nada
        capa = None
        if precisa_capa:
            capa = self._baixar_capa(mbid)
        return RegistroMB("ok", mbid, (informacao.get("title") or None), artista_do_disco(informacao),
                          titulos_das_faixas(informacao), capa, agora)

    def _achar_o_id(self, disco: Album) -> str | None:
        for faixa in disco.tracks[:3]:
            mbid = read_musicbrainz_album_id(faixa.path)
            if mbid and _UUID.match(mbid):
                return mbid                                     # consulta exata
        album = _album_das_tags(disco)
        if not album or not disco.artist:
            return None                                         # sem artista e álbum, sem certeza
        candidatos = self._cliente.procurar_disco(album, disco.artist)
        return escolher_correspondencia(candidatos, album, disco.artist, len(disco.tracks))

    def _baixar_capa(self, mbid: str) -> Path | None:
        dados = self._cliente.capa_frontal(mbid)
        extensao = _formato_da_imagem(dados) if dados else None
        if extensao is None:
            return None
        destino = self._pasta_de_capas / f"{mbid}{extensao}"
        try:
            self._pasta_de_capas.mkdir(parents=True, exist_ok=True)
            descritor, temporario = tempfile.mkstemp(dir=self._pasta_de_capas, suffix=".tmp")
            with os.fdopen(descritor, "wb") as arquivo:
                arquivo.write(dados)
            os.replace(temporario, destino)
        except OSError as erro:
            log.warning("musicbrainz: não consegui gravar a capa: %s", erro)
            return None
        return destino


def _sem_nome_nas_tags(disco: Album) -> bool:
    """True quando o nome do disco veio da pasta, porque nenhuma faixa tem a tag de álbum."""
    return all(t.album is None for t in disco.tracks)


def _album_das_tags(disco: Album) -> str | None:
    nomes = [t.album for t in disco.tracks if t.album]
    return max(set(nomes), key=nomes.count) if nomes else None


# ---------------------------------------------------------------------------
# Aplicar o resultado (na próxima abertura)
# ---------------------------------------------------------------------------

def aplicar(albuns: list[Album], registros: dict[str, RegistroMB]) -> list[Album]:
    """Põe o que veio do MusicBrainz POR CIMA das tags, só onde as tags não dizem nada.

    - o nome do disco, só se nenhuma faixa tem a tag de álbum (o nome veio da pasta);
    - o artista, só se o disco não tem artista;
    - o nome de uma faixa, só se ela não tem título na tag (o nome veio do arquivo) e o
      número de faixas bate com o do MusicBrainz.
    Sem registro, ou com "nada", devolve o disco exatamente como estava.
    """
    resultado = []
    for disco in albuns:
        registro = registros.get(disco.id)
        if registro is None or registro.status != "ok":
            resultado.append(disco)
            continue
        titulo = registro.title if registro.title and _sem_nome_nas_tags(disco) else disco.title
        artista = registro.artist if registro.artist and disco.artist is None else disco.artist
        faixas = disco.tracks
        if registro.track_titles and len(registro.track_titles) == len(faixas):
            faixas = tuple(
                replace(t, title=nome) if nome and t.title == title_from_filename(t.path.stem)[0] else t
                for t, nome in zip(faixas, registro.track_titles))
        resultado.append(replace(disco, title=titulo, artist=artista, tracks=faixas))
    return resultado


def capas_baixadas(registros: dict[str, RegistroMB]) -> dict[str, Path]:
    """As capas do MusicBrainz que existem no disco, por disco (para `refresh_covers`)."""
    return {pasta: r.cover_path for pasta, r in registros.items()
            if r.status == "ok" and r.cover_path is not None and r.cover_path.exists()}
