# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes da cópia de CD, com um gerador de áudio no lugar do CD de verdade."""

import threading

import mutagen.flac

from moa.core import library
from moa.core.ripper import (Copiador, Progresso, Resultado, proximo_nome_de_disco)


def _fonte_falsa(_numero: int) -> str:
    return "audiotestsrc num-buffers=8 samplesperbuffer=1024"


def _copiador(pasta, faixas=3, **extras):
    return Copiador(pasta, fonte=extras.pop("fonte", _fonte_falsa),
                    contar_faixas=lambda: faixas, **extras)


def test_copia_todas_as_faixas_em_flac_com_tags(tmp_path):
    copiador = _copiador(tmp_path)
    assert copiador.copiar() is Resultado.COPIADO
    assert copiador.nome_do_disco == "Disco 1"
    arquivos = sorted(p.name for p in (tmp_path / "Disco 1").iterdir())
    assert arquivos == ["Faixa 01.flac", "Faixa 02.flac", "Faixa 03.flac"]
    tags = mutagen.flac.FLAC(tmp_path / "Disco 1" / "Faixa 02.flac")
    assert tags["title"] == ["Faixa 2"]
    assert tags["album"] == ["Disco 1"]
    assert tags["tracknumber"] == ["2"]


def test_a_estante_enxerga_o_disco_copiado(tmp_path):
    _copiador(tmp_path).copiar()
    discos = library.scan(tmp_path)
    assert [d.title for d in discos] == ["Disco 1"]
    assert len(discos[0].tracks) == 3


def test_nao_deixa_pasta_provisoria_no_fim(tmp_path):
    _copiador(tmp_path).copiar()
    assert [p.name for p in tmp_path.iterdir()] == ["Disco 1"]


def test_nome_pula_numeros_usados_e_provisorios(tmp_path):
    (tmp_path / "Disco 1").mkdir()
    (tmp_path / ".Disco 2.copiando").mkdir()
    (tmp_path / "Disco 4").mkdir()
    assert proximo_nome_de_disco(tmp_path) == "Disco 3"


def test_segunda_copia_vira_disco_2_sem_tocar_no_primeiro(tmp_path):
    _copiador(tmp_path, faixas=1).copiar()
    primeiro = (tmp_path / "Disco 1" / "Faixa 01.flac").read_bytes()
    segundo = _copiador(tmp_path, faixas=1)
    assert segundo.copiar() is Resultado.COPIADO
    assert segundo.nome_do_disco == "Disco 2"
    assert (tmp_path / "Disco 1" / "Faixa 01.flac").read_bytes() == primeiro


def test_sem_disco_nao_cria_nada(tmp_path):
    pasta = tmp_path / "Musica"
    assert _copiador(pasta, faixas=0).copiar() is Resultado.SEM_DISCO
    assert not pasta.exists()


def test_erro_de_leitura_limpa_e_nao_levanta(tmp_path):
    copiador = _copiador(tmp_path, fonte=lambda n: "filesrc location=/nao/existe.wav")
    assert copiador.copiar() is Resultado.FALHOU
    assert list(tmp_path.iterdir()) == []


def test_falha_na_segunda_faixa_nao_deixa_disco_pela_metade(tmp_path):
    def fonte(numero):
        return (_fonte_falsa(numero) if numero == 1
                else "filesrc location=/nao/existe.wav")
    assert _copiador(tmp_path, fonte=fonte).copiar() is Resultado.FALHOU
    assert list(tmp_path.iterdir()) == []


def test_cancelar_antes_de_comecar_limpa(tmp_path):
    copiador = _copiador(tmp_path)
    copiador.cancelar()
    assert copiador.copiar() is Resultado.CANCELADO
    assert list(tmp_path.iterdir()) == []


def test_cancelar_no_meio_limpa(tmp_path):
    copiador = None

    def ao_progredir(p: Progresso):
        if p.faixa == 2:
            copiador.cancelar()

    copiador = _copiador(tmp_path, ao_progredir=ao_progredir)
    assert copiador.copiar() is Resultado.CANCELADO
    assert list(tmp_path.iterdir()) == []


def test_progresso_conta_faixas_de_1_ate_o_total(tmp_path):
    vistos = []
    _copiador(tmp_path, ao_progredir=vistos.append).copiar()
    assert {p.faixa for p in vistos} == {1, 2, 3}
    assert all(p.total == 3 and 0.0 <= p.fracao <= 1.0 for p in vistos)
    assert vistos[-1].fracao == 1.0


def test_copiar_numa_thread_e_cancelar_de_fora(tmp_path):
    copiador = _copiador(tmp_path, faixas=50)
    resultado = []
    fio = threading.Thread(target=lambda: resultado.append(copiador.copiar()))
    fio.start()
    copiador.cancelar()
    fio.join(timeout=30)
    assert resultado == [Resultado.CANCELADO]
    assert list(tmp_path.iterdir()) == []


def test_apaga_sobra_de_copia_interrompida(tmp_path):
    sobra = tmp_path / ".Disco 1.copiando"
    sobra.mkdir()
    (sobra / "Faixa 01.flac").write_bytes(b"x")
    copiador = _copiador(tmp_path, faixas=1)
    assert copiador.copiar() is Resultado.COPIADO
    assert copiador.nome_do_disco == "Disco 1" and not sobra.exists()
