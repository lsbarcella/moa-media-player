# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Testes da rede opcional (M6), contra um servidor HTTP falso na própria máquina.

Nenhum teste fala com a internet de verdade.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from moa.core import musicbrainz as mb
from moa.core.config import Preferencias
from moa.core.contexto import Contexto
from moa.core.db import Database, RegistroMB
from moa.core.library import refresh_library
from moa.core.covers import refresh_covers

ID = "11111111-2222-3333-4444-555555555555"
ID_B = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 64


class Servidor:
    """Servidor falso: `respostas` mapeia o começo do caminho para (código, corpo)."""

    def __init__(self):
        self.respostas: dict[str, tuple[int, bytes]] = {}
        self.pedidos: list[tuple[str, dict]] = []
        dono = self

        class Tratador(BaseHTTPRequestHandler):
            def do_GET(self):
                dono.pedidos.append((self.path, dict(self.headers)))
                for prefixo, (codigo, corpo) in dono.respostas.items():
                    if self.path.startswith(prefixo):
                        self.send_response(codigo)
                        self.end_headers()
                        self.wfile.write(corpo)
                        return
                self.send_response(404)
                self.end_headers()

            def log_message(self, *args):
                pass

        self._http = HTTPServer(("127.0.0.1", 0), Tratador)
        self.url = f"http://127.0.0.1:{self._http.server_port}"
        threading.Thread(target=self._http.serve_forever, daemon=True).start()

    def cliente(self):
        return mb.Cliente(self.url + "/ws/2", self.url, mb.Limitador(0), tempo_limite=3)

    def parar(self):
        self._http.shutdown()
        self._http.server_close()


@pytest.fixture
def servidor():
    s = Servidor()
    yield s
    s.parar()


def release(titulo="Álbum Certo", artista="Ana", faixas=("Um", "Dois"), mbid=ID):
    return json.dumps({
        "id": mbid, "title": titulo,
        "artist-credit": [{"name": artista, "joinphrase": "", "artist": {"name": artista}}],
        "media": [{"tracks": [{"title": t} for t in faixas]}],
    }).encode()


def procura(titulo="Álbum Certo", artista="Ana", total=2, mbid=ID):
    return json.dumps({"releases": [{
        "id": mbid, "title": titulo, "track-count": total,
        "artist-credit": [{"name": artista, "artist": {"name": artista}}]}]}).encode()


@pytest.fixture
def banco(tmp_path):
    b = Database(tmp_path / "moa.db")
    yield b
    b.close()


def montar(tmp_path, make_track, pasta="Disco", n=2, **tags):
    raiz = tmp_path / "musica"
    for i in range(1, n + 1):
        make_track(raiz / pasta, f"{i:02d}.mp3", **tags)
    banco = Database(tmp_path / "moa.db")
    discos = refresh_library(raiz, banco)
    miniaturas = refresh_covers(discos, banco, tmp_path / "min")
    banco.close()
    return raiz, discos, miniaturas


def atualizador(tmp_path, servidor=None, online=True, cliente=None, agora=lambda: 1000.0):
    return mb.Atualizador(tmp_path / "moa.db", tmp_path / "capas", lambda: online,
                          cliente or servidor.cliente(), agora=agora)


# -- cliente -----------------------------------------------------------------------------------

def test_cliente_le_disco_e_capa_e_404_vira_none(servidor):
    servidor.respostas[f"/ws/2/release/{ID}"] = (200, release())
    servidor.respostas[f"/release/{ID}/front-500"] = (200, JPEG)
    c = servidor.cliente()
    assert c.disco_por_id(ID)["title"] == "Álbum Certo"
    assert c.capa_frontal(ID) == JPEG
    assert c.capa_frontal(ID_B) is None          # 404: sem capa, não é erro


def test_o_cabecalho_de_identificacao_e_generico(servidor):
    servidor.respostas["/ws/2/release/"] = (200, release())
    servidor.cliente().disco_por_id(ID)
    agente = servidor.pedidos[0][1]["User-Agent"]
    assert agente == mb.USER_AGENT and "@" not in agente and "/home" not in agente


def test_so_vai_pela_rede_o_id_e_um_id_invalido_nem_e_pedido(servidor):
    c = servidor.cliente()
    assert c.disco_por_id("../../etc/passwd") is None
    assert c.capa_frontal("não é um id") is None
    assert servidor.pedidos == []


@pytest.mark.parametrize("codigo,corpo", [(503, b"fora"), (200, b"isto nao e json"), (200, b"[1, 2]")])
def test_respostas_ruins_viram_erro_de_rede_sem_excecao_de_outro_tipo(servidor, codigo, corpo):
    servidor.respostas["/ws/2/release/"] = (codigo, corpo)
    with pytest.raises(mb.ErroDeRede):
        servidor.cliente().disco_por_id(ID)


def test_servidor_fora_do_ar_vira_erro_de_rede():
    c = mb.Cliente("http://127.0.0.1:1/ws/2", "http://127.0.0.1:1", mb.Limitador(0), tempo_limite=1)
    with pytest.raises(mb.ErroDeRede):
        c.disco_por_id(ID)


def test_limitador_garante_um_pedido_por_segundo():
    agora = [100.0]
    dormiu = []
    lim = mb.Limitador(1.0, relogio=lambda: agora[0], dormir=lambda s: (dormiu.append(s), agora.__setitem__(0, agora[0] + s)))
    lim.esperar()
    agora[0] += 0.25
    lim.esperar()
    assert dormiu == [pytest.approx(0.75)]


# -- o trabalho em segundo plano ---------------------------------------------------------------

def test_com_id_nas_tags_guarda_nome_capa_e_faixas(tmp_path, make_track, servidor):
    servidor.respostas[f"/ws/2/release/{ID}"] = (200, release())
    servidor.respostas[f"/release/{ID}/front-500"] = (200, JPEG)
    _, discos, miniaturas = montar(tmp_path, make_track, musicbrainz_albumid=ID)
    assert atualizador(tmp_path, servidor).executar(discos, miniaturas) == 1
    banco = Database(tmp_path / "moa.db")
    registro = banco.get_mb(discos[0].id)
    banco.close()
    assert registro.status == "ok" and registro.title == "Álbum Certo" and registro.artist == "Ana"
    assert registro.track_titles == ("Um", "Dois")
    assert registro.cover_path.read_bytes() == JPEG


def test_sem_id_so_aceita_nome_artista_e_numero_de_faixas_iguais(tmp_path, make_track, servidor):
    servidor.respostas["/ws/2/release/?"] = (200, procura())
    servidor.respostas[f"/ws/2/release/{ID}"] = (200, release())
    _, discos, miniaturas = montar(tmp_path, make_track, album="Álbum Certo", artist="Ana",
                                   albumartist="Ana")
    assert atualizador(tmp_path, servidor).executar(discos, miniaturas) == 1
    banco = Database(tmp_path / "moa.db")
    assert banco.get_mb(discos[0].id).status == "ok"
    banco.close()


@pytest.mark.parametrize("resposta", [
    procura(titulo="Outro Álbum"), procura(artista="Outra Pessoa"), procura(total=9)])
def test_na_duvida_nao_muda_nada(tmp_path, make_track, servidor, resposta):
    servidor.respostas["/ws/2/release/?"] = (200, resposta)
    _, discos, miniaturas = montar(tmp_path, make_track, album="Álbum Certo", artist="Ana",
                                   albumartist="Ana")
    atualizador(tmp_path, servidor).executar(discos, miniaturas)
    banco = Database(tmp_path / "moa.db")
    registro = banco.get_mb(discos[0].id)
    banco.close()
    assert registro.status == "nada"
    assert mb.aplicar(discos, {discos[0].id: registro}) == discos


def test_disco_sem_nenhuma_tag_e_sem_id_nem_e_consultado(tmp_path, make_track, servidor):
    _, discos, miniaturas = montar(tmp_path, make_track)
    atualizador(tmp_path, servidor).executar(discos, miniaturas)
    assert not any("/ws/2/release/?" in p for p, _ in servidor.pedidos)
    banco = Database(tmp_path / "moa.db")
    assert banco.get_mb(discos[0].id).status == "nada"
    banco.close()


def test_sem_rede_nenhuma_conexao_e_tentada(tmp_path, make_track):
    class ClienteQueNaoPodeSerChamado:
        def __getattr__(self, nome):
            raise AssertionError("tentou usar a rede estando offline")

    _, discos, miniaturas = montar(tmp_path, make_track, musicbrainz_albumid=ID)
    assert atualizador(tmp_path, online=False, cliente=ClienteQueNaoPodeSerChamado()).executar(
        discos, miniaturas) == 0


def test_disco_completo_nao_gera_consulta(tmp_path, make_track, servidor, make_image):
    capa = make_image(tmp_path / "musica" / "Disco" / "folder.jpg")
    _, discos, miniaturas = montar(tmp_path, make_track, album="Completo", artist="Ana",
                                   albumartist="Ana", musicbrainz_albumid=ID)
    assert miniaturas[discos[0].id] is not None and capa.exists()
    assert atualizador(tmp_path, servidor).executar(discos, miniaturas) == 0
    assert servidor.pedidos == []


def test_falha_de_rede_nao_grava_nada_e_tenta_de_novo_na_proxima(tmp_path, make_track, servidor):
    servidor.respostas["/ws/2/release/"] = (503, b"fora")
    _, discos, miniaturas = montar(tmp_path, make_track, musicbrainz_albumid=ID)
    assert atualizador(tmp_path, servidor).executar(discos, miniaturas) == 0
    banco = Database(tmp_path / "moa.db")
    assert banco.get_mb(discos[0].id) is None
    banco.close()


def test_desiste_depois_de_tres_falhas_seguidas(tmp_path, make_track, servidor):
    servidor.respostas["/ws/2/release/"] = (503, b"fora")
    raiz = tmp_path / "musica"
    for nome in "ABCDE":
        make_track(raiz / nome, "01.mp3", musicbrainz_albumid=ID)
    banco = Database(tmp_path / "moa.db")
    discos = refresh_library(raiz, banco)
    banco.close()
    atualizador(tmp_path, servidor).executar(discos, {d.id: None for d in discos})
    assert len(servidor.pedidos) == mb.FALHAS_SEGUIDAS_PARA_DESISTIR


def test_disco_sem_certeza_so_e_reconsultado_depois_de_30_dias(tmp_path, make_track, servidor):
    # O servidor não conhece o disco (404): fica "nada" e não muda coisa alguma.
    _, discos, miniaturas = montar(tmp_path, make_track, musicbrainz_albumid=ID)
    atualizador(tmp_path, servidor, agora=lambda: 1000.0).executar(discos, miniaturas)
    primeiros = len(servidor.pedidos)
    assert primeiros >= 1
    atualizador(tmp_path, servidor, agora=lambda: 2000.0).executar(discos, miniaturas)
    assert len(servidor.pedidos) == primeiros                  # cedo demais
    atualizador(tmp_path, servidor, agora=lambda: 1000.0 + mb.TENTAR_DE_NOVO_APOS + 1).executar(
        discos, miniaturas)
    assert len(servidor.pedidos) > primeiros                   # passados os 30 dias, tenta de novo


def test_imagem_que_nao_e_imagem_nao_vira_capa(tmp_path, make_track, servidor):
    servidor.respostas[f"/ws/2/release/{ID}"] = (200, release())
    servidor.respostas[f"/release/{ID}/front-500"] = (200, b"<html>nao sou imagem</html>")
    _, discos, miniaturas = montar(tmp_path, make_track, musicbrainz_albumid=ID)
    atualizador(tmp_path, servidor).executar(discos, miniaturas)
    banco = Database(tmp_path / "moa.db")
    assert banco.get_mb(discos[0].id).cover_path is None
    banco.close()


# -- aplicar o resultado -----------------------------------------------------------------------

def test_nome_so_muda_quando_a_tag_de_album_falta(tmp_path, make_track):
    _, sem_tag, _ = montar(tmp_path / "a", make_track, pasta="Pasta Feia")
    _, com_tag, _ = montar(tmp_path / "b", make_track, pasta="Outra", album="Nome da Tag")
    for discos in (sem_tag, com_tag):
        registro = RegistroMB("ok", ID, "Nome do MusicBrainz", "Ana", ("Um", "Dois"))
        resultado = mb.aplicar(discos, {discos[0].id: registro})
        esperado = "Nome do MusicBrainz" if discos is sem_tag else "Nome da Tag"
        assert resultado[0].title == esperado


def test_titulo_da_tag_nunca_e_trocado_mas_o_nome_do_arquivo_sim(tmp_path, make_track):
    raiz = tmp_path / "musica" / "D"
    make_track(raiz, "01.mp3", title="Título da Tag")
    make_track(raiz, "Faixa 02.mp3")
    banco = Database(tmp_path / "moa.db")
    discos = refresh_library(tmp_path / "musica", banco)
    banco.close()
    registro = RegistroMB("ok", ID, "X", None, ("MB Um", "MB Dois"))
    titulos = [t.title for t in mb.aplicar(discos, {discos[0].id: registro})[0].tracks]
    assert titulos == ["Título da Tag", "MB Dois"]


def test_numero_de_faixas_diferente_nao_troca_titulos(tmp_path, make_track):
    _, discos, _ = montar(tmp_path, make_track, n=2)
    registro = RegistroMB("ok", ID, "X", None, ("a", "b", "c"))
    antes = [t.title for t in discos[0].tracks]
    assert [t.title for t in mb.aplicar(discos, {discos[0].id: registro})[0].tracks] == antes


# -- na próxima abertura, não durante a sessão -------------------------------------------------

def test_o_resultado_so_aparece_na_proxima_abertura(tmp_path, make_track, make_image):
    raiz, discos, miniaturas = montar(tmp_path, make_track, pasta="Pasta Feia")
    banco = Database(tmp_path / "moa.db")
    capa = make_image(tmp_path / "capa_baixada.jpg")
    ctx = Contexto(banco, Preferencias(tmp_path / "c.json"), raiz, pasta_miniaturas=tmp_path / "min")
    ctx.definir_colecao(discos, miniaturas)
    assert ctx.discos[0].title == "Pasta Feia"

    # a rede traz o resultado no meio da sessão...
    outro = Database(tmp_path / "moa.db")
    outro.save_mb(discos[0].id, RegistroMB("ok", ID, "Nome Bonito", "Ana", (), capa, 1.0))
    outro.close()
    ctx.recarregar(capas=True)
    assert ctx.discos[0].title == "Pasta Feia"            # ...e a estante NÃO muda

    # "abre o app de novo"
    ctx2 = Contexto(banco, Preferencias(tmp_path / "c.json"), raiz, pasta_miniaturas=tmp_path / "min")
    miniaturas2 = refresh_covers(discos, banco, tmp_path / "min", alternativas=mb.capas_baixadas(banco.load_mb()))
    ctx2.definir_colecao(discos, miniaturas2)
    assert ctx2.discos[0].title == "Nome Bonito"
    assert miniaturas2[discos[0].id] is not None            # a capa baixada virou a capa do disco
    banco.close()


def test_a_escolha_do_usuario_vence_o_musicbrainz(tmp_path, make_track):
    from moa.core import box
    raiz, discos, miniaturas = montar(tmp_path, make_track, pasta="Pasta Feia")
    banco = Database(tmp_path / "moa.db")
    banco.save_mb(discos[0].id, RegistroMB("ok", ID, "Nome do MB", "Ana", (), None, 1.0))
    box.guardar_edicao(banco, discos[0].id, "Nome que eu escolhi", None)
    ctx = Contexto(banco, Preferencias(tmp_path / "c.json"), raiz, pasta_miniaturas=tmp_path / "min")
    ctx.definir_colecao(discos, miniaturas)
    assert ctx.discos[0].title == "Nome que eu escolhi"
    banco.close()


def test_capa_da_pasta_vence_a_capa_baixada(tmp_path, make_track, make_image):
    raiz, _, _ = montar(tmp_path, make_track)
    propria = make_image(raiz / "Disco" / "folder.jpg")
    baixada = make_image(tmp_path / "baixada.jpg")
    banco = Database(tmp_path / "moa.db")
    discos = refresh_library(raiz, banco)
    refresh_covers(discos, banco, tmp_path / "min", alternativas={discos[0].id: baixada})
    assert banco.get_cover(discos[0].id).source.path == propria
    banco.close()
