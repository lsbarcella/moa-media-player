# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes da atualização de teste (ADR-0020), sem internet: zip e commit são falsos."""

import zipfile
from pathlib import Path

import pytest

from moa.core.atualizacao_de_teste import (
    AtualizacaoDeTeste, ErroDeAtualizacao, Momento, commit_instalado, instalar_zip,
    pode_atualizar, tem_versao_anterior, voltar_a_versao_anterior)

SHA_A = "a" * 40
SHA_B = "b" * 40


def _montar_pasta(raiz: Path, versao: str) -> None:
    (raiz / "moa").mkdir(parents=True)
    (raiz / "moa" / "__main__.py").write_text(f"VERSAO = {versao!r}\n")
    (raiz / "moa" / "app.py").write_text("")


def _zip(destino: Path, versao: str, *, com_app=True, extra: dict | None = None,
         pasta="moa-media-player-dev") -> Path:
    with zipfile.ZipFile(destino, "w") as z:
        z.writestr(f"{pasta}/moa/__main__.py", f"VERSAO = {versao!r}\n")
        if com_app:
            z.writestr(f"{pasta}/moa/app.py", "")
        for nome, texto in (extra or {}).items():
            z.writestr(nome, texto)
    return destino


def _versao(raiz: Path) -> str:
    return (raiz / "moa" / "__main__.py").read_text()


@pytest.fixture
def raiz(tmp_path):
    pasta = tmp_path / "app"
    _montar_pasta(pasta, "velha")
    return pasta


def test_instalar_troca_a_pasta_e_guarda_a_anterior(raiz, tmp_path):
    instalar_zip(_zip(tmp_path / "a.zip", "nova"), raiz, SHA_A)
    assert "nova" in _versao(raiz)
    assert "velha" in (raiz / "moa.anterior" / "__main__.py").read_text()
    assert commit_instalado(raiz) == SHA_A
    assert not (raiz / ".moa-novo").exists()


def test_voltar_desfaz_a_ultima_atualizacao(raiz, tmp_path):
    instalar_zip(_zip(tmp_path / "a.zip", "nova"), raiz, SHA_A)
    voltar_a_versao_anterior(raiz)
    assert "velha" in _versao(raiz)
    assert "nova" in (raiz / "moa.anterior" / "__main__.py").read_text()
    assert commit_instalado(raiz) is None


def test_voltar_sem_anterior_da_erro(raiz):
    with pytest.raises(ErroDeAtualizacao):
        voltar_a_versao_anterior(raiz)


@pytest.mark.parametrize("zip_ruim", [
    lambda d: _zip(d, "x", com_app=False),
    lambda d: _zip(d, "x", extra={"outra/arquivo.txt": "oi"}),
    lambda d: _zip(d, "x", extra={"moa-media-player-dev/../fora.txt": "oi"}),
    lambda d: _zip(d, "x", extra={"moa-media-player-dev/moa/quebrado.py": "def (:\n"}),
])
def test_zip_ruim_nao_muda_nada(raiz, tmp_path, zip_ruim):
    with pytest.raises(ErroDeAtualizacao):
        instalar_zip(zip_ruim(tmp_path / "ruim.zip"), raiz, SHA_A)
    assert "velha" in _versao(raiz)
    assert not tem_versao_anterior(raiz) and not (raiz / ".moa-novo").exists()


def test_nao_atualiza_instalacao_do_sistema():
    assert pode_atualizar(Path("/usr/lib/moa")) is False


def test_pasta_normal_pode(raiz):
    assert pode_atualizar(raiz) is True


def _atualizacao(raiz, tmp_path, remoto=SHA_B, zip_pronto=None):
    def baixar(destino):
        destino.write_bytes((zip_pronto or _zip(tmp_path / "dev.zip", "nova")).read_bytes())
    return AtualizacaoDeTeste(raiz, buscar_commit=lambda: remoto, baixar_zip=baixar)


def test_procura_e_acha_versao_nova(raiz, tmp_path):
    (raiz / ".moa-commit").write_text(SHA_A + "\n")
    a = _atualizacao(raiz, tmp_path)
    a.verificar()
    a.thread.join(10)
    assert a.momento == Momento.HA_NOVA and a.commit_remoto == SHA_B
    assert "aaaaaaa" in a.versao_em_texto() and "bbbbbbb" in a.versao_em_texto()


def test_procura_e_ja_esta_atualizado(raiz, tmp_path):
    (raiz / ".moa-commit").write_text(SHA_B + "\n")
    a = _atualizacao(raiz, tmp_path)
    a.verificar()
    a.thread.join(10)
    assert a.momento == Momento.ATUALIZADO


def test_fluxo_completo_ate_pronto(raiz, tmp_path):
    a = _atualizacao(raiz, tmp_path)
    estados = []
    a.ao_mudar(lambda: estados.append(a.momento))
    a.verificar()
    a.thread.join(10)
    a.instalar()
    a.thread.join(10)
    assert estados == [Momento.PROCURANDO, Momento.HA_NOVA, Momento.BAIXANDO, Momento.PRONTO]
    assert "nova" in _versao(raiz) and commit_instalado(raiz) == SHA_B


def test_sem_internet_falha_calmo_na_busca_manual(raiz, tmp_path):
    def sem_rede():
        raise OSError("sem rede")
    a = AtualizacaoDeTeste(raiz, buscar_commit=sem_rede)
    a.verificar()
    a.thread.join(10)
    assert a.momento == Momento.FALHOU and "Tudo continua como estava" in a.frase()


def test_sem_internet_na_busca_silenciosa_nao_mostra_nada(raiz, tmp_path):
    def sem_rede():
        raise OSError("sem rede")
    a = AtualizacaoDeTeste(raiz, buscar_commit=sem_rede)
    a.verificar(silenciosa=True)
    a.thread.join(10)
    assert a.momento == Momento.INATIVO


def test_download_com_erro_mantem_a_versao_atual(raiz, tmp_path):
    def baixar_quebrado(destino):
        raise OSError("caiu a conexão")
    a = AtualizacaoDeTeste(raiz, buscar_commit=lambda: SHA_B, baixar_zip=baixar_quebrado)
    a.verificar()
    a.thread.join(10)
    a.instalar()
    a.thread.join(10)
    assert a.momento == Momento.FALHOU
    assert "velha" in _versao(raiz) and not tem_versao_anterior(raiz)


def test_desligada_fora_de_pasta_de_codigo(tmp_path):
    vazia = tmp_path / "vazia"
    vazia.mkdir()
    a = AtualizacaoDeTeste(vazia, buscar_commit=lambda: SHA_B)
    assert a.habilitada is False
    a.verificar()
    assert a.momento == Momento.INATIVO and a.thread is None
