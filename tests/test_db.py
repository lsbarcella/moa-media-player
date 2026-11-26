"""Testes do banco SQLite (M1, parte 4)."""

import sqlite3
from pathlib import Path

import pytest

from estante.core.covers import CoverSource
from estante.core.db import MIGRACOES, Database, EsquemaMaisNovoQueOApp
from estante.core.models import Track


def faixa(nome="/m/CD/01.mp3", **campos):
    base = dict(path=Path(nome), title="Samba", mtime=1700000000.5, size=1234)
    base.update(campos)
    return Track(**base)


@pytest.fixture
def db():
    banco = Database(":memory:")
    yield banco
    banco.close()


# ---------------------------------------------------------------------------
# Esquema e migrações
# ---------------------------------------------------------------------------

def test_banco_novo_ja_nasce_na_versao_mais_recente(db):
    assert db.schema_version() == len(MIGRACOES)


def test_reabrir_nao_refaz_a_migracao_e_guarda_os_dados(tmp_path):
    caminho = tmp_path / "estante.db"
    primeiro = Database(caminho)
    primeiro.save_tracks([faixa()])
    primeiro.close()
    segundo = Database(caminho)
    assert segundo.schema_version() == len(MIGRACOES)
    assert list(segundo.load_tracks()) == ["/m/CD/01.mp3"]
    segundo.close()


# ---------------------------------------------------------------------------
# Faixas
# ---------------------------------------------------------------------------

def test_faixa_vai_e_volta_igual(db):
    original = faixa(number=3, artist="Zeca", album="Sambas", album_artist="Zeca")
    db.save_tracks([original])
    assert db.load_tracks()["/m/CD/01.mp3"] == original


def test_campos_vazios_voltam_como_none(db):
    db.save_tracks([faixa()])
    lida = db.load_tracks()["/m/CD/01.mp3"]
    assert (lida.number, lida.artist, lida.album, lida.album_artist) == (None, None, None, None)


def test_acentos_e_caminhos_com_espacos_sobrevivem(db):
    original = faixa("/música/Clássicos do Samba/05 - Ponteio.mp3", title="Ponteio — ao vivo")
    db.save_tracks([original])
    assert db.load_tracks()[str(original.path)] == original


def test_gravar_de_novo_substitui_a_faixa(db):
    db.save_tracks([faixa(title="Antigo")])
    db.save_tracks([faixa(title="Novo")])
    carregadas = db.load_tracks()
    assert len(carregadas) == 1
    assert carregadas["/m/CD/01.mp3"].title == "Novo"


def test_esquece_as_faixas_que_sumiram(db):
    db.save_tracks([faixa("/m/a.mp3"), faixa("/m/b.mp3"), faixa("/m/c.mp3")])
    db.delete_tracks_except(["/m/a.mp3", "/m/c.mp3"])
    assert sorted(db.load_tracks()) == ["/m/a.mp3", "/m/c.mp3"]


def test_esquecer_tudo_quando_a_lista_e_vazia(db):
    db.save_tracks([faixa()])
    db.delete_tracks_except([])
    assert db.load_tracks() == {}


def test_esquecer_funciona_com_milhares_de_faixas(db):
    # o SQLite limita quantos valores cabem numa consulta; a tabela temporária contorna isso
    db.save_tracks([faixa(f"/m/{i}.mp3") for i in range(5000)])
    db.delete_tracks_except(f"/m/{i}.mp3" for i in range(0, 5000, 2))
    assert len(db.load_tracks()) == 2500


def test_gravacao_interrompida_no_meio_nao_deixa_nada_pela_metade(db):
    def faixas_com_defeito():
        yield faixa("/m/a.mp3")
        yield faixa("/m/b.mp3")
        raise RuntimeError("queda de energia simulada")

    with pytest.raises(RuntimeError):
        db.save_tracks(faixas_com_defeito())
    assert db.load_tracks() == {}      # a transação foi desfeita


# ---------------------------------------------------------------------------
# Capas
# ---------------------------------------------------------------------------

def test_registro_de_capa_com_fonte_e_miniatura(db):
    fonte = CoverSource("embedded", Path("/m/CD/01.mp3"))
    db.save_cover("/m/CD", "abc", fonte, Path("/cache/x.png"))
    registro = db.get_cover("/m/CD")
    assert (registro.signature, registro.source, registro.thumbnail) == (
        "abc", fonte, Path("/cache/x.png"))


def test_registro_de_disco_sem_capa(db):
    db.save_cover("/m/CD", "abc", None, None)
    registro = db.get_cover("/m/CD")
    assert (registro.source, registro.thumbnail) == (None, None)


def test_capa_desconhecida_devolve_none(db):
    assert db.get_cover("/m/nao-existe") is None


def test_esquece_as_capas_de_discos_que_sumiram(db):
    for pasta in ("/m/a", "/m/b"):
        db.save_cover(pasta, "x", None, None)
    db.delete_covers_except(["/m/a"])
    assert db.get_cover("/m/a") is not None and db.get_cover("/m/b") is None


# ---------------------------------------------------------------------------
# Recuperação de problemas: o idoso nunca vê um erro técnico
# ---------------------------------------------------------------------------

def test_banco_corrompido_e_guardado_ao_lado_e_um_novo_e_criado(tmp_path):
    caminho = tmp_path / "estante.db"
    caminho.write_bytes(b"isto nao e um banco sqlite " * 100)
    db = Database.open(caminho)                       # não pode levantar erro
    assert db.schema_version() == len(MIGRACOES)
    assert db.load_tracks() == {}
    db.close()
    guardados = list(tmp_path.glob("estante.db.problema-*"))
    assert len(guardados) == 1                        # o arquivo ruim foi guardado, não apagado
    assert guardados[0].read_bytes().startswith(b"isto nao e um banco")


def test_banco_de_versao_futura_tambem_e_guardado_ao_lado(tmp_path):
    caminho = tmp_path / "estante.db"
    conexao = sqlite3.connect(caminho)
    conexao.execute(f"PRAGMA user_version = {len(MIGRACOES) + 5}")
    conexao.execute("CREATE TABLE coisa_do_futuro(x)")
    conexao.commit()
    conexao.close()
    with pytest.raises(EsquemaMaisNovoQueOApp):
        Database(caminho)
    db = Database.open(caminho)
    assert db.schema_version() == len(MIGRACOES)
    db.close()
    assert len(list(tmp_path.glob("estante.db.problema-*"))) == 1


def test_banco_ocupado_nao_e_tratado_como_corrompido(tmp_path):
    caminho = tmp_path / "estante.db"
    Database(caminho).close()
    trancador = sqlite3.connect(caminho, isolation_level=None)
    trancador.execute("BEGIN EXCLUSIVE")              # outro processo segurando o banco
    try:
        with pytest.raises(sqlite3.OperationalError):
            Database.open(caminho, timeout=0.1)       # espera pouco, para o teste ser rápido
    finally:
        trancador.execute("ROLLBACK")
        trancador.close()
    assert list(tmp_path.glob("estante.db.problema-*")) == []   # o arquivo bom não foi movido
    assert caminho.exists()


def test_cria_a_pasta_do_banco_se_ela_nao_existe(tmp_path):
    db = Database.open(tmp_path / "ainda" / "nao" / "existe" / "estante.db")
    db.close()
    assert (tmp_path / "ainda" / "nao" / "existe" / "estante.db").exists()
