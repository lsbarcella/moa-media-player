# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes da Lixeira, das edições e do "Apagar de vez" (M4). Só pastas temporárias."""

import os
import stat
from pathlib import Path

import pytest

from moa.core import box, custom_albums as ca
from moa.core.covers import CoverChoice, refresh_covers
from moa.core.db import Database
from moa.core.library import refresh_library, scan


@pytest.fixture
def db(tmp_path):
    banco = Database(tmp_path / "moa.db")
    yield banco
    banco.close()


@pytest.fixture
def colecao(make_track, make_image, tmp_path):
    raiz = tmp_path / "musica"
    for album in ("Boleros", "Valsas", "Tangos"):
        for n in (1, 2):
            make_track(raiz / album, f"{n:02d}.mp3", title=f"{album} {n}", album=album,
                       artist="Ana", tracknumber=str(n))
    make_image(raiz / "Boleros" / "folder.jpg")
    return raiz


def por_titulo(discos, titulo):
    return next(d for d in discos if d.title == titulo)


def arvore(raiz):
    return sorted(str(p.relative_to(raiz)) for p in raiz.rglob("*"))


# -- camadas ----------------------------------------------------------------------------------

def test_sem_nada_guardado_as_camadas_nao_mudam_o_resultado(db, colecao):
    albuns = refresh_library(colecao, db)
    camadas = box.aplicar_camadas(albuns, [], db)
    assert camadas.estante == albuns and camadas.caixa == [] and camadas.montados == []


def test_tirar_da_estante_some_na_abertura_seguinte_e_colocar_de_volta_traz_de_volta(db, colecao):
    antes = arvore(colecao)
    albuns = refresh_library(colecao, db)
    box.tirar_da_estante(db, por_titulo(albuns, "Tangos").id)
    # "Reabrir o app": nova varredura e novas camadas.
    camadas = box.aplicar_camadas(refresh_library(colecao, db), [], db)
    assert sorted(d.title for d in camadas.estante) == ["Boleros", "Valsas"]
    assert [d.title for d in camadas.caixa] == ["Tangos"]
    box.colocar_de_volta(db, por_titulo(albuns, "Tangos").id)
    assert len(box.aplicar_camadas(refresh_library(colecao, db), [], db).estante) == 3
    assert arvore(colecao) == antes                      # nenhum arquivo mudou


def test_disco_montado_tambem_vai_para_a_caixa(db, colecao):
    albuns = refresh_library(colecao, db)
    faixas = {str(t.path): t for d in albuns for t in d.tracks}
    mix_id = ca.criar(db, "Mix", [str(albuns[0].tracks[0].path)])
    montados = ca.carregar(db, faixas)
    box.tirar_da_estante(db, mix_id)
    camadas = box.aplicar_camadas(albuns, montados, db)
    assert camadas.montados == [] and [m.id for m in camadas.caixa] == [mix_id]


# -- nome e capa ------------------------------------------------------------------------------------

def test_renomear_guarda_o_valor_antigo_e_como_era_antes_restaura_uma_vez(db, colecao):
    albuns = refresh_library(colecao, db)
    disco = por_titulo(albuns, "Boleros")
    box.guardar_edicao(db, disco.id, "Os Boleros do Pai", None)
    camadas = box.aplicar_camadas(albuns, [], db)
    assert "Os Boleros do Pai" in [d.title for d in camadas.estante]
    assert box.como_era_antes(db, disco.id) is True
    assert "Boleros" in [d.title for d in box.aplicar_camadas(albuns, [], db).estante]
    assert box.como_era_antes(db, disco.id) is False


def test_dois_nomes_seguidos_como_era_antes_volta_so_um_passo(db, colecao):
    disco = por_titulo(refresh_library(colecao, db), "Valsas")
    box.guardar_edicao(db, disco.id, "Um", None)
    box.guardar_edicao(db, disco.id, "Dois", None)
    assert box.como_era_antes(db, disco.id) is True
    assert db.get_override(disco.id).name == "Um"


def test_nome_vazio_mantem_o_nome_atual_e_nao_vira_antes(db, colecao):
    disco = por_titulo(refresh_library(colecao, db), "Valsas")
    box.guardar_edicao(db, disco.id, "Novo", None)
    box.guardar_edicao(db, disco.id, "   ", None)
    assert db.get_override(disco.id).name == "Novo"
    assert db.get_override(disco.id).prev_name is None      # nada mudou na segunda chamada


def test_capa_trocada_vale_na_abertura_seguinte_e_a_miniatura_antiga_some(db, colecao, make_image, tmp_path):
    cache = tmp_path / "cache"
    albuns = refresh_library(colecao, db)
    disco = por_titulo(albuns, "Boleros")
    antes = refresh_covers(albuns, db, cache)[disco.id]
    assert antes is not None and antes.exists()                # tinha o folder.jpg
    box.guardar_edicao(db, disco.id, None, CoverChoice("drawn"))
    depois = refresh_covers(albuns, db, cache, escolhas=box.escolhas_de_capa(db))[disco.id]
    assert depois is None                                       # capa desenhada: sem miniatura
    assert not antes.exists()                                   # a miniatura antiga foi descartada
    box.como_era_antes(db, disco.id)
    de_novo = refresh_covers(albuns, db, cache, escolhas=box.escolhas_de_capa(db))[disco.id]
    assert de_novo is not None and de_novo.exists()


def test_escolher_a_imagem_da_pasta_vira_a_fonte_da_capa(db, colecao, tmp_path):
    albuns = refresh_library(colecao, db)
    disco = por_titulo(albuns, "Valsas")
    imagem = colecao / "Boleros" / "folder.jpg"                  # qualquer imagem existente
    box.guardar_edicao(db, disco.id, None, CoverChoice("file", imagem))
    mini = refresh_covers(albuns, db, tmp_path / "c", escolhas=box.escolhas_de_capa(db))[disco.id]
    assert mini is not None and mini.exists()


# -- apagar de vez ------------------------------------------------------------------------------------

def test_apagar_de_vez_remove_so_audio_e_capa_daquela_pasta(db, colecao):
    albuns = refresh_library(colecao, db)
    disco = por_titulo(albuns, "Boleros")
    box.tirar_da_estante(db, disco.id)
    resultado = box.apagar_de_vez(db, disco, colecao)
    assert resultado.apagou_tudo and resultado.apagados == 3          # 2 faixas + folder.jpg
    assert not (colecao / "Boleros").exists()                         # ficou vazia: some
    assert (colecao / "Valsas" / "01.mp3").exists() and (colecao / "Tangos").is_dir()   # vizinhas intactas
    assert colecao.is_dir()                                           # a pasta pai fica
    assert disco.id not in db.load_box()


def test_apagar_de_vez_mantem_a_pasta_se_sobrou_outro_arquivo_do_usuario(db, colecao):
    albuns = refresh_library(colecao, db)
    disco = por_titulo(albuns, "Valsas")
    (colecao / "Valsas" / "encarte.pdf").write_bytes(b"x")
    resultado = box.apagar_de_vez(db, disco, colecao)
    assert resultado.apagou_tudo
    assert (colecao / "Valsas" / "encarte.pdf").exists()


def test_apagar_de_vez_nao_apaga_arquivo_de_audio_que_nao_e_do_disco(db, colecao):
    albuns = refresh_library(colecao, db)
    disco = por_titulo(albuns, "Valsas")
    (colecao / "Valsas" / "outra.mp3").write_bytes(b"nao e deste disco")
    # O disco foi lido antes de "outra.mp3" existir: ela não faz parte das faixas dele.
    box.apagar_de_vez(db, disco, colecao)
    assert (colecao / "Valsas" / "outra.mp3").exists()


def test_apagar_de_vez_recusa_pasta_fora_da_raiz_da_musica(db, colecao, make_track, tmp_path):
    fora = tmp_path / "documentos"
    make_track(fora / "Tudo", "01.mp3", title="Importante")
    [disco] = scan(fora)
    resultado = box.apagar_de_vez(db, disco, colecao)
    assert not resultado.apagou_tudo and resultado.recusado
    assert (fora / "Tudo" / "01.mp3").exists()


def test_apagar_de_vez_recusa_link_simbolico_para_fora(db, colecao, make_track, tmp_path):
    fora = tmp_path / "documentos"
    make_track(fora / "Tudo", "01.mp3", title="Importante")
    link = colecao / "atalho"
    link.symlink_to(fora / "Tudo", target_is_directory=True)
    [disco] = [d for d in scan(colecao) if d.folder.name == "atalho"] or [None]
    if disco is None:                                         # a varredura nem segue o link: ótimo
        return
    resultado = box.apagar_de_vez(db, disco, colecao)
    assert not resultado.apagou_tudo
    assert (fora / "Tudo" / "01.mp3").exists()


def test_apagar_de_vez_recusa_a_propria_raiz_e_o_que_nao_e_um_disco(db, colecao):
    from moa.core.models import Album
    raiz_como_disco = Album(folder=colecao, title="Tudo", tracks=scan(colecao)[0].tracks)
    assert box.apagar_de_vez(db, raiz_como_disco, colecao).recusado
    assert box.apagar_de_vez(db, Album(folder=colecao / "Boleros", title="X", tracks=()), colecao).recusado
    assert (colecao / "Boleros" / "01.mp3").exists()


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignora permissões de pasta")
def test_falha_no_meio_deixa_o_disco_na_caixa_com_o_que_sobrou(db, colecao):
    albuns = refresh_library(colecao, db)
    disco = por_titulo(albuns, "Tangos")
    box.tirar_da_estante(db, disco.id)
    pasta = colecao / "Tangos"
    pasta.chmod(stat.S_IRUSR | stat.S_IXUSR)                  # sem permissão de apagar dentro
    try:
        resultado = box.apagar_de_vez(db, disco, colecao)
    finally:
        pasta.chmod(stat.S_IRWXU)
    assert not resultado.apagou_tudo and resultado.restantes == 2
    assert disco.id in db.load_box()                           # continua na Lixeira
    assert (colecao / "Valsas" / "01.mp3").exists()            # nada fora da pasta foi tocado


def test_apagar_de_vez_um_disco_montado_so_apaga_o_registro(db, colecao):
    albuns = refresh_library(colecao, db)
    mix_id = ca.criar(db, "Mix", [str(albuns[0].tracks[0].path)])
    montados = ca.carregar(db, {str(t.path): t for d in albuns for t in d.tracks})
    box.tirar_da_estante(db, mix_id)
    resultado = box.apagar_de_vez(db, montados[0], colecao)
    assert resultado.apagou_tudo
    assert ca.carregar(db, {}) == [] and mix_id not in db.load_box()
    assert all(t.path.exists() for d in albuns for t in d.tracks)


def test_apagar_de_vez_nunca_apaga_faixa_que_aponta_para_fora_da_pasta_do_disco(db, colecao):
    from dataclasses import replace
    albuns = refresh_library(colecao, db)
    boleros, valsas = por_titulo(albuns, "Boleros"), por_titulo(albuns, "Valsas")
    # Um disco "defeituoso": uma das faixas aponta para o disco vizinho.
    estranho = replace(boleros, tracks=boleros.tracks + (valsas.tracks[0],))
    box.apagar_de_vez(db, estranho, colecao)
    assert valsas.tracks[0].path.exists()
    assert not (colecao / "Boleros" / "01.mp3").exists()      # as dele foram apagadas
