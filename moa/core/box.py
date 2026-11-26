# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""A Caixa e as edições de nome e capa (M4). Sem GTK.

Tudo aqui é uma CAMADA sobre a biblioteca (KTD10): a varredura continua lendo as
pastas, e depois `aplicar_camadas` esconde os discos da Caixa e troca nomes. Assim
um disco tirado não volta na abertura seguinte e nenhuma tag nem arquivo de música
é reescrito.

"Apagar de vez" é a única operação que apaga arquivos do usuário. Por isso tem
regras de segurança (ADR-0012, KTD11) e é testada só com pastas temporárias.
"""

import logging
import os
from dataclasses import dataclass, replace
from pathlib import Path

from moa.core.covers import _EXTENSOES, _NOMES, CoverChoice
from moa.core.custom_albums import apagar as apagar_montado
from moa.core.custom_albums import eh_disco_montado
from moa.core.db import Database, Override
from moa.core.models import Album, MixDisc

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Camadas:
    estante: list          # discos (Album) que aparecem na estante, com os nomes editados
    montados: list         # discos montados (MixDisc) que aparecem na estante
    caixa: list            # discos e discos montados que estão na Caixa


def aplicar_camadas(albuns: list[Album], montados: list[MixDisc], db: Database) -> Camadas:
    """Esconde os discos da Caixa e aplica os nomes escolhidos. Sem nada guardado, devolve o mesmo."""
    na_caixa = set(db.load_box())
    nomes = {i: o.name for i, o in db.load_overrides().items() if o.name}

    def com_nome(disco):
        return replace(disco, title=nomes[disco.id]) if disco.id in nomes else disco

    albuns = [com_nome(a) for a in albuns]
    montados = [com_nome(m) for m in montados]
    return Camadas(
        estante=[a for a in albuns if a.id not in na_caixa],
        montados=[m for m in montados if m.id not in na_caixa],
        caixa=[d for d in albuns + montados if d.id in na_caixa],
    )


def escolhas_de_capa(db: Database) -> dict[str, CoverChoice]:
    """As capas que o usuário escolheu, prontas para `refresh_covers`."""
    return {i: CoverChoice(o.cover_kind, Path(o.cover_path) if o.cover_path else None)
            for i, o in db.load_overrides().items() if o.cover_kind}


# -- Caixa -----------------------------------------------------------------------------------

def tirar_da_estante(db: Database, disco_id: str) -> None:
    """O disco vai para a Caixa. Nenhum arquivo muda."""
    db.put_in_box(disco_id)


def colocar_de_volta(db: Database, disco_id: str) -> None:
    db.take_out_of_box(disco_id)


# -- Nome e capa ---------------------------------------------------------------------------------

def guardar_edicao(db: Database, disco_id: str, nome: str | None, capa: CoverChoice | None) -> None:
    """Guarda o nome e/ou a capa novos, lembrando os de antes para "Como era antes".

    `nome` vazio ou só espaços mantém o nome atual. `capa` None mantém a capa atual.
    """
    atual = db.get_override(disco_id) or Override()
    novo_nome = nome.strip() if nome and nome.strip() else atual.name
    if capa is not None:
        tipo, caminho = capa.kind, (str(capa.path) if capa.path else None)
    else:
        tipo, caminho = atual.cover_kind, atual.cover_path
    if (novo_nome, tipo, caminho) == (atual.name, atual.cover_kind, atual.cover_path):
        return                                   # nada mudou: não vira "antes"
    db.save_override(disco_id, Override(
        name=novo_nome, cover_kind=tipo, cover_path=caminho,
        prev_name=atual.name, prev_cover_kind=atual.cover_kind, prev_cover_path=atual.cover_path,
        has_prev=True))


def como_era_antes(db: Database, disco_id: str) -> bool:
    """Restaura o nome e a capa de antes da última edição. Só vale uma vez (False na segunda)."""
    atual = db.get_override(disco_id)
    if atual is None or not atual.has_prev:
        return False
    if (atual.prev_name, atual.prev_cover_kind, atual.prev_cover_path) == (None, None, None):
        db.delete_override(disco_id)
    else:
        db.save_override(disco_id, Override(
            name=atual.prev_name, cover_kind=atual.prev_cover_kind, cover_path=atual.prev_cover_path))
    return True


# -- Apagar de vez -----------------------------------------------------------------------------------

@dataclass(frozen=True)
class ResultadoDoApagar:
    apagou_tudo: bool
    apagados: int = 0
    restantes: int = 0
    recusado: str | None = None      # motivo técnico (só para o log), quando nada foi apagado


def _dentro_de(pasta: Path, raiz: Path) -> bool:
    try:
        pasta.resolve().relative_to(raiz.resolve())
    except ValueError:
        return False
    return pasta.resolve() != raiz.resolve()


def _arquivos_de_capa(pasta: Path) -> list[Path]:
    try:
        presentes = {e.name.lower(): Path(e.path) for e in os.scandir(pasta) if e.is_file(follow_symlinks=False)}
    except OSError:
        return []
    return [presentes[n + e] for n in _NOMES for e in _EXTENSOES if n + e in presentes]


def apagar_de_vez(db: Database, disco, raiz_da_musica: Path) -> ResultadoDoApagar:
    """Apaga o disco da Caixa. É a ÚNICA função que apaga arquivos de música do usuário.

    Regras (KTD11):
    - disco montado: só o registro é apagado; nenhum arquivo é tocado;
    - disco de verdade: só os arquivos de áudio das faixas dele e as imagens de capa
      da PRÓPRIA pasta; nunca a pasta pai, nunca nada fora da pasta de música,
      nunca um link simbólico; a pasta só some se ficar vazia;
    - se alguma remoção falhar, o disco continua na Caixa com o que sobrou.
    """
    if eh_disco_montado(disco.id):
        apagar_montado(db, disco.id)
        _esquecer(db, disco.id)
        return ResultadoDoApagar(True)

    if not isinstance(disco, Album) or not disco.tracks:
        return _recusar(f"{getattr(disco, 'id', disco)} não é um disco")
    pasta = Path(disco.folder)
    if pasta.is_symlink() or not pasta.is_dir():
        return _recusar(f"{pasta} é um link simbólico ou não existe")
    if not _dentro_de(pasta, raiz_da_musica):
        return _recusar(f"{pasta} está fora da pasta de música")

    alvos = [t.path for t in disco.tracks] + _arquivos_de_capa(pasta)
    apagados = 0
    for arquivo in alvos:
        if arquivo.parent.resolve() != pasta.resolve() or arquivo.is_symlink():
            log.warning("recusei apagar %s: não é um arquivo comum desta pasta", arquivo)
            continue
        try:
            arquivo.unlink()
            apagados += 1
        except FileNotFoundError:
            pass                                  # já tinha sumido
        except OSError as erro:
            log.error("não consegui apagar %s: %s", arquivo, erro)

    restantes = sum(1 for t in disco.tracks if t.path.exists())
    if restantes == 0:
        try:
            pasta.rmdir()                         # só funciona se a pasta ficou vazia
        except OSError:
            pass                                  # sobrou outro arquivo do usuário: fica
        _esquecer(db, disco.id)
        return ResultadoDoApagar(True, apagados)
    return ResultadoDoApagar(False, apagados, restantes)


def _recusar(motivo: str) -> ResultadoDoApagar:
    log.error("apagar de vez recusado: %s", motivo)
    return ResultadoDoApagar(False, 0, 0, motivo)


def _esquecer(db: Database, disco_id: str) -> None:
    db.take_out_of_box(disco_id)
    db.delete_override(disco_id)
