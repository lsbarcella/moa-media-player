# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Banco de dados SQLite do Moa (ADR-0008). Sem GTK.

Hoje guarda só o cache da biblioteca (faixas e capas). Nos próximos marcos
entram os discos montados, a Caixa, os recentes e onde o idoso parou, como
novas migrações.

Princípios:
- O banco NUNCA vira mensagem técnica para o idoso (restrição 5). Se o arquivo
  estiver corrompido, ele é guardado ao lado com outro nome e um banco novo é
  criado. O cache se refaz sozinho varrendo as pastas.
- As gravações acontecem dentro de transações: ou entra tudo, ou nada. Isso
  importa num notebook antigo que pode ser desligado de repente.
- Só usamos o `sqlite3` que já vem no Python (sem dependência nova).
"""

import logging
import os
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from moa.core.covers import CoverSource
from moa.core.models import Track

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Migrações: a lista cresce, nunca se edita uma migração que já foi entregue.
# O número da versão fica gravado dentro do próprio arquivo (PRAGMA user_version).
# É como as migrações de banco de um app web, só que sem ferramenta externa.
# ---------------------------------------------------------------------------

def _migracao_1(conexao: sqlite3.Connection) -> None:
    conexao.execute("""
        CREATE TABLE tracks (
            path         TEXT PRIMARY KEY,   -- identidade da faixa: o caminho do arquivo
            mtime        REAL NOT NULL,      -- data de modificação (para saber se mudou)
            size         INTEGER NOT NULL,   -- tamanho em bytes (idem)
            title        TEXT NOT NULL,
            number       INTEGER,
            artist       TEXT,
            album        TEXT,
            album_artist TEXT
        )""")
    conexao.execute("""
        CREATE TABLE covers (
            folder    TEXT PRIMARY KEY,      -- pasta do disco
            signature TEXT NOT NULL,         -- muda quando o disco muda
            kind      TEXT,                  -- 'embedded', 'file' ou NULL (sem capa)
            path      TEXT,                  -- de onde vem a capa
            thumbnail TEXT                   -- miniatura pronta, ou NULL
        )""")


def _migracao_2(conexao: sqlite3.Connection) -> None:
    """Onde o idoso parou e os discos ouvidos há pouco (M2). Aditiva: não toca no M1."""
    conexao.execute("""
        CREATE TABLE playback (
            id          INTEGER PRIMARY KEY CHECK (id = 1),   -- uma linha só
            album_id    TEXT NOT NULL,
            track_index INTEGER NOT NULL,
            seconds     REAL NOT NULL
        )""")
    conexao.execute("""
        CREATE TABLE recent_albums (
            album_id  TEXT PRIMARY KEY,
            played_at REAL NOT NULL
        )""")


def _migracao_3(conexao: sqlite3.Connection) -> None:
    """Discos montados, Caixa e edições de nome e capa (M4). Aditiva."""
    conexao.execute("""
        CREATE TABLE mix_discs (
            id         TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            created_at REAL NOT NULL
        )""")
    conexao.execute("""
        CREATE TABLE mix_tracks (
            mix_id   TEXT NOT NULL,
            position INTEGER NOT NULL,
            path     TEXT NOT NULL,           -- faixa de outro disco: só a referência
            PRIMARY KEY (mix_id, position)
        )""")
    conexao.execute("""
        CREATE TABLE box (
            album_id TEXT PRIMARY KEY,        -- disco tirado da estante (a Caixa)
            put_at   REAL NOT NULL
        )""")
    conexao.execute("""
        CREATE TABLE overrides (
            album_id        TEXT PRIMARY KEY,
            name            TEXT,             -- nome escolhido pelo usuário (NULL: o original)
            cover_kind      TEXT,             -- 'embedded', 'file' ou 'drawn' (NULL: automática)
            cover_path      TEXT,
            prev_name       TEXT,             -- valores de antes da última edição
            prev_cover_kind TEXT,
            prev_cover_path TEXT,
            has_prev        INTEGER NOT NULL DEFAULT 0
        )""")


MIGRACOES = [_migracao_1, _migracao_2, _migracao_3]


class EsquemaMaisNovoQueOApp(Exception):
    """O arquivo foi criado por uma versão mais nova do app."""


@dataclass(frozen=True)
class Override:
    """Nome e capa escolhidos pelo usuário para um disco, com o valor de antes."""

    name: str | None = None
    cover_kind: str | None = None
    cover_path: str | None = None
    prev_name: str | None = None
    prev_cover_kind: str | None = None
    prev_cover_path: str | None = None
    has_prev: bool = False


@dataclass(frozen=True)
class CoverRecord:
    """O que o cache sabe sobre a capa de um disco."""

    signature: str
    source: CoverSource | None      # None: o disco não tem capa (usa a substituta)
    thumbnail: Path | None          # None: não há miniatura (usa a substituta)


class Database:
    def __init__(self, caminho: Path | str, timeout: float = 5.0):
        # isolation_level=None: nós mesmos abrimos e fechamos as transações
        # (ver `_transacao`), em vez de deixar o Python decidir quando.
        # timeout: quanto esperar se outro processo estiver usando o banco.
        self._conexao = sqlite3.connect(str(caminho), timeout=timeout, isolation_level=None)
        try:
            self._migrar()
        except BaseException:
            self._conexao.close()
            raise

    @classmethod
    def open(cls, caminho: Path | str, timeout: float = 5.0) -> "Database":
        """Abre o banco, recuperando-se sozinho de um arquivo corrompido.

        Um arquivo ilegível não é apagado: vai para `<nome>.problema-<hora>`,
        caso valha a pena examiná-lo depois. Já um banco apenas "ocupado"
        (outro processo usando) não é tratado como corrompido.
        """
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        try:
            return cls(caminho, timeout)
        except sqlite3.OperationalError:
            raise                       # ocupado, sem permissão etc.: não é corrupção
        except (sqlite3.DatabaseError, EsquemaMaisNovoQueOApp) as erro:
            guardado = caminho.with_name(f"{caminho.name}.problema-{int(time.time())}")
            log.error("banco ilegível (%s); guardei em %s e vou criar um novo", erro, guardado)
            os.replace(caminho, guardado)
            return cls(caminho, timeout)

    def close(self) -> None:
        self._conexao.close()

    # -- infraestrutura ------------------------------------------------------

    @contextmanager
    def _transacao(self):
        """Tudo o que acontecer dentro do `with` entra junto ou não entra."""
        self._conexao.execute("BEGIN")
        try:
            yield
        except BaseException:
            self._conexao.execute("ROLLBACK")
            raise
        else:
            self._conexao.execute("COMMIT")

    def _migrar(self) -> None:
        versao = self._conexao.execute("PRAGMA user_version").fetchone()[0]
        if versao > len(MIGRACOES):
            raise EsquemaMaisNovoQueOApp(f"versão {versao}, o app conhece até {len(MIGRACOES)}")
        for n in range(versao, len(MIGRACOES)):
            with self._transacao():
                MIGRACOES[n](self._conexao)
                self._conexao.execute(f"PRAGMA user_version = {n + 1}")

    def schema_version(self) -> int:
        return self._conexao.execute("PRAGMA user_version").fetchone()[0]

    def _apagar_exceto(self, tabela: str, coluna: str, valores: Iterable[str]) -> None:
        """Apaga as linhas cuja `coluna` não está em `valores`.

        Usa uma tabela temporária porque o SQLite limita quantos valores cabem
        numa única consulta. (Os nomes de tabela e coluna vêm só do nosso código.)
        """
        with self._transacao():
            self._conexao.execute("CREATE TEMP TABLE IF NOT EXISTS manter(chave TEXT PRIMARY KEY)")
            self._conexao.execute("DELETE FROM manter")
            self._conexao.executemany("INSERT OR IGNORE INTO manter VALUES (?)", ((v,) for v in valores))
            self._conexao.execute(f"DELETE FROM {tabela} WHERE {coluna} NOT IN (SELECT chave FROM manter)")

    # -- cache das faixas ----------------------------------------------------

    def load_tracks(self) -> dict[str, Track]:
        """Todas as faixas do cache, pelo caminho. Para 800 faixas leva ~1 ms."""
        linhas = self._conexao.execute(
            "SELECT path, mtime, size, title, number, artist, album, album_artist FROM tracks")
        return {
            caminho: Track(path=Path(caminho), mtime=mtime, size=tamanho, title=titulo,
                           number=numero, artist=artista, album=album, album_artist=artista_album)
            for caminho, mtime, tamanho, titulo, numero, artista, album, artista_album in linhas
        }

    def save_tracks(self, faixas: Iterable[Track]) -> None:
        """Grava as faixas (as que já existem são substituídas), numa transação."""
        with self._transacao():
            self._conexao.executemany(
                "INSERT OR REPLACE INTO tracks VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ((str(t.path), t.mtime, t.size, t.title, t.number, t.artist, t.album, t.album_artist)
                 for t in faixas))

    def delete_tracks_except(self, caminhos: Iterable[str]) -> None:
        """Esquece as faixas que não estão mais na pasta de música."""
        self._apagar_exceto("tracks", "path", caminhos)

    # -- onde parou e recentes (M2) -------------------------------------------

    def save_playback(self, album_id: str, indice: int, segundos: float) -> None:
        with self._transacao():
            self._conexao.execute(
                "INSERT OR REPLACE INTO playback VALUES (1, ?, ?, ?)", (album_id, indice, segundos))

    def load_playback(self) -> tuple[str, int, float] | None:
        linha = self._conexao.execute(
            "SELECT album_id, track_index, seconds FROM playback WHERE id = 1").fetchone()
        return (linha[0], linha[1], linha[2]) if linha else None

    def touch_recent(self, album_id: str, limite: int) -> None:
        """Põe o disco como o mais novo dos recentes e guarda só os `limite` últimos."""
        with self._transacao():
            self._conexao.execute(
                "INSERT OR REPLACE INTO recent_albums VALUES (?, ?)", (album_id, time.time()))
            self._conexao.execute(
                "DELETE FROM recent_albums WHERE album_id NOT IN "
                "(SELECT album_id FROM recent_albums ORDER BY played_at DESC, rowid DESC LIMIT ?)",
                (limite,))

    def load_recents(self) -> list[str]:
        """Do mais novo para o mais antigo."""
        linhas = self._conexao.execute(
            "SELECT album_id FROM recent_albums ORDER BY played_at DESC, rowid DESC")
        return [linha[0] for linha in linhas]

    # -- discos montados (M4) ---------------------------------------------------

    def create_mix(self, mix_id: str, nome: str, caminhos: list[str]) -> None:
        with self._transacao():
            self._conexao.execute("INSERT INTO mix_discs VALUES (?, ?, ?)", (mix_id, nome, time.time()))
            self._conexao.executemany(
                "INSERT INTO mix_tracks VALUES (?, ?, ?)",
                ((mix_id, posicao, caminho) for posicao, caminho in enumerate(caminhos)))

    def add_mix_track(self, mix_id: str, caminho: str) -> bool:
        """Põe a faixa no fim do disco montado. False se ela já estava (não duplica)."""
        with self._transacao():
            ja_tem = self._conexao.execute(
                "SELECT 1 FROM mix_tracks WHERE mix_id = ? AND path = ?", (mix_id, caminho)).fetchone()
            if ja_tem:
                return False
            proxima = self._conexao.execute(
                "SELECT COALESCE(MAX(position) + 1, 0) FROM mix_tracks WHERE mix_id = ?",
                (mix_id,)).fetchone()[0]
            self._conexao.execute("INSERT INTO mix_tracks VALUES (?, ?, ?)", (mix_id, proxima, caminho))
            return True

    def remove_mix_track(self, mix_id: str, caminho: str) -> None:
        with self._transacao():
            self._conexao.execute("DELETE FROM mix_tracks WHERE mix_id = ? AND path = ?", (mix_id, caminho))

    def delete_mix(self, mix_id: str) -> None:
        with self._transacao():
            self._conexao.execute("DELETE FROM mix_tracks WHERE mix_id = ?", (mix_id,))
            self._conexao.execute("DELETE FROM mix_discs WHERE id = ?", (mix_id,))

    def load_mixes(self) -> list[tuple[str, str, list[str]]]:
        """(id, nome, caminhos das faixas na ordem escolhida) de cada disco montado."""
        discos = self._conexao.execute("SELECT id, name FROM mix_discs ORDER BY created_at, id").fetchall()
        resultado = []
        for mix_id, nome in discos:
            caminhos = [linha[0] for linha in self._conexao.execute(
                "SELECT path FROM mix_tracks WHERE mix_id = ? ORDER BY position", (mix_id,))]
            resultado.append((mix_id, nome, caminhos))
        return resultado

    # -- Caixa e edições (M4) -----------------------------------------------------

    def put_in_box(self, album_id: str) -> None:
        with self._transacao():
            self._conexao.execute("INSERT OR REPLACE INTO box VALUES (?, ?)", (album_id, time.time()))

    def take_out_of_box(self, album_id: str) -> None:
        with self._transacao():
            self._conexao.execute("DELETE FROM box WHERE album_id = ?", (album_id,))

    def load_box(self) -> list[str]:
        return [linha[0] for linha in self._conexao.execute("SELECT album_id FROM box ORDER BY put_at, album_id")]

    def get_override(self, album_id: str) -> Override | None:
        linha = self._conexao.execute(
            "SELECT name, cover_kind, cover_path, prev_name, prev_cover_kind, prev_cover_path, has_prev "
            "FROM overrides WHERE album_id = ?", (album_id,)).fetchone()
        return Override(*linha[:6], bool(linha[6])) if linha else None

    def load_overrides(self) -> dict[str, Override]:
        linhas = self._conexao.execute(
            "SELECT album_id, name, cover_kind, cover_path, prev_name, prev_cover_kind, prev_cover_path, "
            "has_prev FROM overrides")
        return {l[0]: Override(*l[1:7], bool(l[7])) for l in linhas}

    def save_override(self, album_id: str, valor: Override) -> None:
        with self._transacao():
            self._conexao.execute(
                "INSERT OR REPLACE INTO overrides VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (album_id, valor.name, valor.cover_kind, valor.cover_path, valor.prev_name,
                 valor.prev_cover_kind, valor.prev_cover_path, int(valor.has_prev)))

    def delete_override(self, album_id: str) -> None:
        with self._transacao():
            self._conexao.execute("DELETE FROM overrides WHERE album_id = ?", (album_id,))

    # -- cache das capas -----------------------------------------------------

    def get_cover(self, pasta: str) -> CoverRecord | None:
        linha = self._conexao.execute(
            "SELECT signature, kind, path, thumbnail FROM covers WHERE folder = ?", (pasta,)).fetchone()
        if linha is None:
            return None
        assinatura, tipo, caminho, miniatura = linha
        fonte = CoverSource(tipo, Path(caminho)) if tipo else None
        return CoverRecord(assinatura, fonte, Path(miniatura) if miniatura else None)

    def save_cover(self, pasta: str, assinatura: str, fonte: CoverSource | None,
                   miniatura: Path | None) -> None:
        with self._transacao():
            self._conexao.execute(
                "INSERT OR REPLACE INTO covers VALUES (?, ?, ?, ?, ?)",
                (pasta, assinatura, fonte.kind if fonte else None,
                 str(fonte.path) if fonte else None, str(miniatura) if miniatura else None))

    def delete_covers_except(self, pastas: Iterable[str]) -> None:
        self._apagar_exceto("covers", "folder", pastas)
