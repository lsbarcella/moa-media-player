# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes da atualização de teste (ADR-0020), sem internet: zip e commit são falsos."""

import zipfile
from pathlib import Path

import pytest

from moa.core.atualizacao_de_teste import (
    AtualizacaoDeTeste, ErroDeAtualizacao, Momento, commit_instalado, formatar_bytes, instalar_zip,
    pode_atualizar, tem_versao_anterior, voltar_a_versao_anterior)

SHA_A = "a" * 40
SHA_B = "b" * 40


def _montar_pasta(raiz: Path, versao: str, com_tools: bool = True) -> None:
    (raiz / "moa").mkdir(parents=True)
    if com_tools:
        (raiz / "tools").mkdir()
        (raiz / "tools" / "check_deps.sh").write_text("antigo\n")
    (raiz / "moa" / "__main__.py").write_text(f"VERSAO = {versao!r}\n")
    (raiz / "moa" / "app.py").write_text("")


def _zip(destino: Path, versao: str, *, com_app=True, extra: dict | None = None,
         pasta="moa-media-player-dev", com_tools=True) -> Path:
    with zipfile.ZipFile(destino, "w") as z:
        z.writestr(f"{pasta}/moa/__main__.py", f"VERSAO = {versao!r}\n")
        if com_tools:
            z.writestr(f"{pasta}/tools/measure.sh", "novo\n")
            z.writestr(f"{pasta}/tools/check_deps.sh", "novo\n")
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


def _atualizacao(raiz, tmp_path, remoto=SHA_B, zip_pronto=None, tamanho=1_300_000):
    def baixar(destino, ao_progredir=None):
        dados = (zip_pronto or _zip(tmp_path / "dev.zip", "nova")).read_bytes()
        destino.write_bytes(dados)
        if ao_progredir is not None:
            ao_progredir(len(dados) // 2)
            ao_progredir(len(dados))
    return AtualizacaoDeTeste(raiz, buscar_commit=lambda: remoto, baixar_zip=baixar,
                              buscar_tamanho=lambda _sha: tamanho, pausa=0)


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
    assert estados == [Momento.PROCURANDO, Momento.HA_NOVA, Momento.BAIXANDO, Momento.INSTALANDO,
                       Momento.PRONTO]
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
    def baixar_quebrado(destino, ao_progredir=None):
        raise OSError("caiu a conexão")
    a = AtualizacaoDeTeste(raiz, buscar_commit=lambda: SHA_B, baixar_zip=baixar_quebrado,
                           buscar_tamanho=lambda _sha: None, pausa=0)
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


def test_atualiza_tambem_a_pasta_tools_e_guarda_a_anterior(raiz, tmp_path):
    instalar_zip(_zip(tmp_path / "a.zip", "nova"), raiz, SHA_A)
    assert (raiz / "tools" / "measure.sh").read_text() == "novo\n"
    assert (raiz / "tools" / "check_deps.sh").read_text() == "novo\n"
    assert (raiz / "tools.anterior" / "check_deps.sh").read_text() == "antigo\n"
    assert not (raiz / "tools.anterior" / "measure.sh").exists()


def test_voltar_devolve_tambem_a_pasta_tools(raiz, tmp_path):
    instalar_zip(_zip(tmp_path / "a.zip", "nova"), raiz, SHA_A)
    voltar_a_versao_anterior(raiz)
    assert (raiz / "tools" / "check_deps.sh").read_text() == "antigo\n"
    assert not (raiz / "tools" / "measure.sh").exists()
    assert (raiz / "tools.anterior" / "measure.sh").exists()
    assert not (raiz / ".tools-troca").exists()


def test_instala_mesmo_sem_pasta_tools_antiga(tmp_path):
    pasta = tmp_path / "app"
    _montar_pasta(pasta, "velha", com_tools=False)
    instalar_zip(_zip(tmp_path / "a.zip", "nova"), pasta, SHA_A)
    assert "nova" in _versao(pasta) and (pasta / "tools" / "measure.sh").exists()
    assert not (pasta / "tools.anterior").exists()


def test_zip_sem_tools_atualiza_so_o_app(raiz, tmp_path):
    instalar_zip(_zip(tmp_path / "a.zip", "nova", com_tools=False), raiz, SHA_A)
    assert "nova" in _versao(raiz)
    assert (raiz / "tools" / "check_deps.sh").read_text() == "antigo\n"


def test_falha_na_troca_de_tools_nao_impede_a_atualizacao(raiz, tmp_path, monkeypatch):
    from moa.core import atualizacao_de_teste as modulo
    original = modulo._trocar_pasta

    def quebra_so_tools(nova, atual, anterior):
        if atual.name == "tools":
            raise OSError("sem permissão")
        original(nova, atual, anterior)
    monkeypatch.setattr(modulo, "_trocar_pasta", quebra_so_tools)
    instalar_zip(_zip(tmp_path / "a.zip", "nova"), raiz, SHA_A)
    assert "nova" in _versao(raiz) and commit_instalado(raiz) == SHA_A
    assert (raiz / "tools" / "check_deps.sh").read_text() == "antigo\n"


# -- o feedback: tamanho, download, instalação -------------------------------------------------

def test_formata_o_tamanho_em_palavras():
    assert formatar_bytes(None) == "tamanho desconhecido"
    assert formatar_bytes(900) == "900 bytes"
    assert formatar_bytes(344226) == "336 KB"
    assert formatar_bytes(1_300_000) == "1,2 MB"


def test_ao_achar_versao_nova_mostra_o_tamanho_aproximado(raiz, tmp_path):
    a = _atualizacao(raiz, tmp_path, tamanho=1_300_000)
    a.verificar()
    a.thread.join(10)
    assert a.momento == Momento.HA_NOVA and a.tamanho_estimado == 1_300_000
    assert a.tamanho_em_texto() == "Tamanho aproximado: 1,2 MB (descompactado)"


def test_sem_saber_o_tamanho_nao_inventa(raiz, tmp_path):
    a = _atualizacao(raiz, tmp_path, tamanho=None)
    a.verificar()
    a.thread.join(10)
    assert a.momento == Momento.HA_NOVA and a.tamanho_em_texto() == ""


def test_o_download_conta_os_bytes_e_a_instalacao_conta_as_etapas(raiz, tmp_path):
    a = _atualizacao(raiz, tmp_path)
    a.verificar()
    a.thread.join(10)
    vistos = []
    a.ao_progredir(lambda: vistos.append((a.momento, a.bytes_baixados, a.etapa_da_instalacao)))
    a.instalar()
    a.thread.join(10)
    baixando = [v for v in vistos if v[0] == Momento.BAIXANDO]
    assert baixando and baixando[0][1] > 0 and baixando[-1][1] >= baixando[0][1]
    instalando = [v[2] for v in vistos if v[0] == Momento.INSTALANDO]
    assert instalando == ["conferindo os arquivos", "trocando os arquivos do aplicativo",
                          "trocando as ferramentas", "guardando a versão instalada"]
    assert a.tamanho_do_pacote == a.bytes_baixados > 0
    assert a.tamanho_em_texto().startswith("Tamanho da atualização:")


def test_as_etapas_vao_de_aguardando_a_feita(raiz, tmp_path):
    a = _atualizacao(raiz, tmp_path)
    a.verificar()
    a.thread.join(10)
    assert [m for m, _t in a.etapas()] == ["○", "○", "○"]
    marcas = []
    a.ao_mudar(lambda: marcas.append((a.momento, [m for m, _t in a.etapas()])))
    a.instalar()
    a.thread.join(10)
    por_momento = dict(marcas)
    assert por_momento[Momento.BAIXANDO] == ["→", "○", "○"]
    assert por_momento[Momento.INSTALANDO] == ["✓", "→", "○"]
    assert por_momento[Momento.PRONTO] == ["✓", "✓", "→"]
    assert "Reinicie o aplicativo" in a.etapas()[2][1]


def test_a_barra_so_enche_na_instalacao_e_chega_a_um_no_fim(raiz, tmp_path):
    a = _atualizacao(raiz, tmp_path)
    a.verificar()
    a.thread.join(10)
    assert a.fracao() is None
    fracoes = []
    a.ao_progredir(lambda: fracoes.append((a.momento, a.fracao())))
    a.instalar()
    a.thread.join(10)
    assert all(f is None for m, f in fracoes if m == Momento.BAIXANDO)       # total desconhecido
    instalando = [f for m, f in fracoes if m == Momento.INSTALANDO]
    assert instalando == sorted(instalando) and 0 < instalando[0] <= instalando[-1] <= 1
    assert a.fracao() == 1.0


def test_instalar_zip_conta_as_etapas_e_so_confere_se_o_zip_for_ruim(raiz, tmp_path):
    etapas = []
    instalar_zip(_zip(tmp_path / "a.zip", "nova"), raiz, SHA_A, etapas.append)
    assert etapas == ["conferindo os arquivos", "trocando os arquivos do aplicativo",
                      "trocando as ferramentas", "guardando a versão instalada"]
    etapas.clear()
    with pytest.raises(ErroDeAtualizacao):
        instalar_zip(_zip(tmp_path / "ruim.zip", "x", com_app=False), raiz, SHA_A, etapas.append)
    assert etapas == ["conferindo os arquivos"]


def test_ocupada_vale_tambem_para_instalando(raiz, tmp_path):
    a = _atualizacao(raiz, tmp_path)
    a.momento = Momento.INSTALANDO
    assert a.ocupada
