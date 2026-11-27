# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes do Aparelho de CD (estados e textos), com um gerador de áudio no lugar do CD."""

from moa.core.aparelho import MSG_FALHOU, MSG_SEM_DISCO, AparelhoDeCD, Momento


def _fonte(_n: int) -> str:
    return "audiotestsrc num-buffers=8 samplesperbuffer=1024"


def _aparelho(pasta, faixas=3, fonte=_fonte, **extras):
    return AparelhoDeCD(pasta, fonte=fonte, contar_faixas=lambda: faixas, **extras)


def _copiar_e_esperar(aparelho):
    aparelho.copiar()
    aparelho.thread.join(timeout=30)


def test_comeca_esperando_o_cd():
    visor = AparelhoDeCD(".").visor()
    assert visor.texto == "ABRA A GAVETA E PONHA O CD"
    assert visor.fracao is None


def test_copiar_ate_o_fim_mostra_pronto_e_avisa_a_estante(tmp_path):
    aparelho = _aparelho(tmp_path)
    chamadas = []
    aparelho.ao_copiar(lambda: chamadas.append("reler"))
    _copiar_e_esperar(aparelho)
    assert aparelho.momento == Momento.PRONTO
    assert aparelho.nome_do_disco == "Disco 1"
    assert aparelho.visor().texto == "PRONTO: 3 músicas"
    assert "Disco 1" in aparelho.visor().explicacao
    assert chamadas == ["reler"]
    assert (tmp_path / "Disco 1").is_dir()


def test_visor_mostra_a_faixa_durante_a_copia(tmp_path):
    vistos = []
    aparelho = _aparelho(tmp_path)
    aparelho.ao_mudar(lambda: vistos.append(aparelho.visor()))
    _copiar_e_esperar(aparelho)
    textos = {v.texto for v in vistos}
    assert "COPIANDO: Faixa 2 de 3" in textos
    assert all(0.0 <= v.fracao <= 1.0 for v in vistos if v.fracao is not None)


def test_sem_disco(tmp_path):
    aparelho = _aparelho(tmp_path, faixas=0)
    _copiar_e_esperar(aparelho)
    assert aparelho.momento == Momento.SEM_DISCO
    assert aparelho.visor().texto == "SEM DISCO NO APARELHO"
    assert aparelho.visor().explicacao == MSG_SEM_DISCO


def test_falha_na_leitura(tmp_path):
    aparelho = _aparelho(tmp_path, fonte=lambda n: "filesrc location=/nao/existe.wav")
    _copiar_e_esperar(aparelho)
    assert aparelho.momento == Momento.FALHOU
    assert aparelho.visor().explicacao == MSG_FALHOU
    assert list(tmp_path.iterdir()) == []


def test_parar_volta_ao_comeco_e_nao_deixa_nada(tmp_path):
    aparelho = _aparelho(tmp_path, faixas=50)
    aparelho.copiar()
    aparelho.parar()
    aparelho.thread.join(timeout=30)
    assert aparelho.momento == Momento.INICIO
    assert list(tmp_path.iterdir()) == []


def test_tentar_de_novo_depois_de_sem_disco(tmp_path):
    contagem = {"faixas": 0}
    aparelho = AparelhoDeCD(tmp_path, fonte=_fonte, contar_faixas=lambda: contagem["faixas"])
    _copiar_e_esperar(aparelho)
    assert aparelho.momento == Momento.SEM_DISCO
    contagem["faixas"] = 2
    _copiar_e_esperar(aparelho)
    assert aparelho.momento == Momento.PRONTO


def test_recomecar_volta_ao_inicio_sem_apagar_o_disco(tmp_path):
    aparelho = _aparelho(tmp_path)
    _copiar_e_esperar(aparelho)
    aparelho.recomecar()
    assert aparelho.momento == Momento.INICIO
    assert (tmp_path / "Disco 1").is_dir()


def test_nao_comeca_duas_copias_ao_mesmo_tempo(tmp_path):
    aparelho = _aparelho(tmp_path, faixas=50)
    aparelho.copiar()
    primeira = aparelho.thread
    aparelho.copiar()
    assert aparelho.thread is primeira
    aparelho.encerrar()


def test_encerrar_cancela_e_espera(tmp_path):
    aparelho = _aparelho(tmp_path, faixas=50)
    aparelho.copiar()
    aparelho.encerrar()
    assert not aparelho.thread.is_alive()
    assert list(tmp_path.iterdir()) == []


def test_gaveta_usa_a_funcao_de_ejetar():
    chamadas = []
    aparelho = AparelhoDeCD(".", ejetar=lambda: chamadas.append(1) or True)
    assert aparelho.abrir_a_gaveta() is True
    assert chamadas == [1]


def test_erro_ao_reler_a_estante_nao_derruba(tmp_path):
    aparelho = _aparelho(tmp_path)
    aparelho.ao_copiar(lambda: 1 / 0)
    _copiar_e_esperar(aparelho)
    assert aparelho.momento == Momento.PRONTO
