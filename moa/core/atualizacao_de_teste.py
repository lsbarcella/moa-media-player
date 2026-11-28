# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""ATUALIZAÇÃO DE TESTE (TEMPORÁRIA, REMOVER ANTES DA VERSÃO FINAL, ADR-0020).

Deixa o autor atualizar o app no notebook de testes com a branch `dev` do GitHub:
procura um commit novo, baixa o zip da `dev`, confere, troca a pasta `moa/` (guardando
a anterior em `moa.anterior/`) e pede para reiniciar. Sem GTK.

Só funciona quando o app roda de uma pasta que o usuário pode escrever (`python3 -m moa`
a partir do zip ou do clone). Instalado pelo .deb (`/usr/lib/moa`) ela se desliga sozinha.

Para o autor (vem de TypeScript): `buscar_commit` e `baixar_zip` são funções injetadas,
como callbacks, para os testes não precisarem de internet.
"""

import compileall
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile
from enum import Enum
from pathlib import Path
from typing import Callable

import moa

log = logging.getLogger(__name__)

REPOSITORIO = "lsbarcella/moa-media-player"
RAMO = "dev"
URL_DO_COMMIT = f"https://api.github.com/repos/{REPOSITORIO}/commits/{RAMO}"
URL_DO_ZIP = f"https://codeload.github.com/{REPOSITORIO}/zip/refs/heads/{RAMO}"
AGENTE = "MoaMediaPlayer/0.1"       # genérico: nenhum dado pessoal
LIMITE_DO_ZIP = 100 * 1024 * 1024
_SHA = re.compile(r"^[0-9a-f]{40}$")
ARQUIVO_DO_COMMIT = ".moa-commit"
PAUSA_ENTRE_ETAPAS = 0.6        # cada passo fica visível um instante, para dar para acompanhar
ETAPAS_DA_INSTALACAO = 4        # conferir, trocar o app, trocar as ferramentas, guardar a versão


class ErroDeAtualizacao(Exception):
    pass


class Momento(Enum):
    INATIVO = "inativo"
    PROCURANDO = "procurando"
    ATUALIZADO = "atualizado"       # já está na versão mais nova
    HA_NOVA = "ha_nova"
    BAIXANDO = "baixando"
    INSTALANDO = "instalando"
    PRONTO = "pronto"               # instalada; falta reiniciar
    FALHOU = "falhou"


FRASES = {
    Momento.INATIVO: "Aqui você busca uma versão mais nova do app (só no ambiente de testes).",
    Momento.PROCURANDO: "Procurando uma versão mais nova…",
    Momento.ATUALIZADO: "Você já está com a versão mais nova.",
    Momento.HA_NOVA: "Tem uma versão mais nova do app.",
    Momento.BAIXANDO: "Baixando a atualização. Pode esperar.",
    Momento.INSTALANDO: "Instalando a versão nova. Pode esperar.",
    Momento.PRONTO: "Pronto! A versão nova está instalada. Reinicie o aplicativo para usá-la.",
    Momento.FALHOU: "Não consegui atualizar agora. Tudo continua como estava.",
}


def formatar_bytes(n: int | float | None) -> str:
    """"340 KB", "1,2 MB": o tamanho em palavras que dá para ler de relance."""
    if n is None:
        return "tamanho desconhecido"
    if n < 1024:
        return f"{int(n)} bytes"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n / (1024 * 1024):.1f} MB".replace(".", ",")


# -- o que existe na pasta -------------------------------------------------------------------

def raiz_do_app() -> Path:
    return Path(moa.__file__).resolve().parent.parent


def pode_atualizar(raiz: Path) -> bool:
    """Só atualiza uma pasta de código-fonte que o usuário pode escrever (nunca /usr)."""
    return ((raiz / "moa" / "__main__.py").is_file() and os.access(raiz, os.W_OK)
            and not str(raiz).startswith("/usr/"))


def commit_instalado(raiz: Path) -> str | None:
    arquivo = raiz / ARQUIVO_DO_COMMIT
    if arquivo.is_file():
        texto = arquivo.read_text(encoding="utf-8").strip()
        return texto if _SHA.match(texto) else None
    if (raiz / ".git").exists():
        try:
            saida = subprocess.run(["git", "-C", str(raiz), "rev-parse", "HEAD"], timeout=3,
                                   capture_output=True, text=True).stdout.strip()
            return saida if _SHA.match(saida) else None
        except (OSError, subprocess.SubprocessError):
            return None
    return None


def tem_versao_anterior(raiz: Path) -> bool:
    return (raiz / "moa.anterior" / "__main__.py").is_file()


# -- a internet (trocável nos testes) --------------------------------------------------------

def buscar_commit_remoto() -> str:
    pedido = urllib.request.Request(
        URL_DO_COMMIT, headers={"User-Agent": AGENTE, "Accept": "application/vnd.github.sha"})
    with urllib.request.urlopen(pedido, timeout=10) as resposta:
        sha = resposta.read(100).decode("ascii", "replace").strip()
    if not _SHA.match(sha):
        raise ErroDeAtualizacao(f"resposta inesperada do GitHub: {sha[:40]!r}")
    return sha


def baixar_zip_remoto(destino: Path, ao_progredir: Callable[[int], None] | None = None) -> None:
    """Baixa o zip da `dev`. O GitHub manda o arquivo em partes, sem avisar o tamanho total
    antes, então só se sabe quanto já veio (`ao_progredir(bytes_baixados)`, no máximo 10 vezes
    por segundo)."""
    pedido = urllib.request.Request(URL_DO_ZIP, headers={"User-Agent": AGENTE})
    total, ultimo = 0, 0.0
    with urllib.request.urlopen(pedido, timeout=60) as resposta, open(destino, "wb") as saida:
        while bloco := resposta.read(16 * 1024):
            total += len(bloco)
            if total > LIMITE_DO_ZIP:
                raise ErroDeAtualizacao("o arquivo baixado é grande demais")
            saida.write(bloco)
            agora = time.monotonic()
            if ao_progredir is not None and agora - ultimo >= 0.1:
                ultimo = agora
                ao_progredir(total)
    if ao_progredir is not None:
        ao_progredir(total)


def tamanho_remoto(sha: str) -> int | None:
    """Quanto o repositório ocupa, sem compactar (soma dos arquivos daquela versão), para dar uma
    ideia do tamanho antes de baixar. O zip baixado é menor. Falha em silêncio (None)."""
    try:
        pedido = urllib.request.Request(
            f"https://api.github.com/repos/{REPOSITORIO}/git/trees/{sha}?recursive=1",
            headers={"User-Agent": AGENTE, "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(pedido, timeout=10) as resposta:
            dados = json.loads(resposta.read(5 * 1024 * 1024))
        return sum(e.get("size", 0) for e in dados.get("tree", []) if e.get("type") == "blob")
    except Exception:
        log.info("não consegui saber o tamanho da atualização", exc_info=True)
        return None


# -- a troca da pasta --------------------------------------------------------------------------

def _trocar_pasta(nova: Path, atual: Path, anterior: Path) -> None:
    """`atual` vira `anterior` e `nova` vira `atual`. Se a segunda troca falhar, desfaz a primeira."""
    shutil.rmtree(anterior, ignore_errors=True)
    tinha = atual.exists()
    if tinha:
        os.rename(atual, anterior)
    try:
        os.rename(nova, atual)
    except OSError:
        if tinha:
            os.rename(anterior, atual)
        raise


def instalar_zip(arquivo_zip: Path, raiz: Path, commit: str,
                 ao_etapa: Callable[[str], None] | None = None) -> None:
    """Confere o zip e troca `moa/` (e `tools/`) pela versão nova. Se algo falhar, nada muda.

    `moa/` é o app e é obrigatório. `tools/` (medição, scripts) acompanha a `dev`, mas se a troca
    dele falhar a atualização vale mesmo assim.

    `ao_etapa(texto)` conta em que passo está ("conferindo os arquivos", "trocando..."), para a
    tela mostrar a instalação andando.
    """
    etapa = ao_etapa or (lambda _texto: None)
    etapa("conferindo os arquivos")
    novo = raiz / ".moa-novo"
    shutil.rmtree(novo, ignore_errors=True)
    novo.mkdir()
    try:
        with zipfile.ZipFile(arquivo_zip) as z:
            nomes = z.namelist()
            if any(n.startswith("/") or ".." in Path(n).parts for n in nomes):
                raise ErroDeAtualizacao("o zip tem caminhos suspeitos")
            pastas = {n.split("/")[0] for n in nomes}
            if len(pastas) != 1:
                raise ErroDeAtualizacao("o zip não tem o formato esperado")
            z.extractall(novo)
        base = novo / pastas.pop()
        pacote = base / "moa"
        if not (pacote / "__main__.py").is_file() or not (pacote / "app.py").is_file():
            raise ErroDeAtualizacao("o zip não tem o aplicativo")
        if not compileall.compile_dir(str(pacote), quiet=2, force=True):
            raise ErroDeAtualizacao("a versão nova tem erro de sintaxe")
        etapa("trocando os arquivos do aplicativo")
        _trocar_pasta(pacote, raiz / "moa", raiz / "moa.anterior")
        if (base / "tools").is_dir():
            etapa("trocando as ferramentas")
            try:
                _trocar_pasta(base / "tools", raiz / "tools", raiz / "tools.anterior")
            except OSError:
                log.exception("não consegui atualizar a pasta tools; o app foi atualizado mesmo assim")
        etapa("guardando a versão instalada")
        (raiz / ARQUIVO_DO_COMMIT).write_text(commit + "\n", encoding="utf-8")
    finally:
        shutil.rmtree(novo, ignore_errors=True)


def voltar_a_versao_anterior(raiz: Path) -> None:
    """Troca `moa/` e `moa.anterior/` de lugar (desfaz a última atualização)."""
    atual, anterior, temporaria = raiz / "moa", raiz / "moa.anterior", raiz / ".moa-troca"
    if not tem_versao_anterior(raiz):
        raise ErroDeAtualizacao("não há versão anterior")
    shutil.rmtree(temporaria, ignore_errors=True)
    os.rename(atual, temporaria)
    os.rename(anterior, atual)
    os.rename(temporaria, anterior)
    if (raiz / "tools.anterior").is_dir():
        try:
            _trocar_pasta(raiz / "tools.anterior", raiz / "tools", raiz / ".tools-troca")
            os.rename(raiz / ".tools-troca", raiz / "tools.anterior")
        except OSError:
            log.exception("não consegui voltar a pasta tools")
    (raiz / ARQUIVO_DO_COMMIT).unlink(missing_ok=True)       # a versão de antes não tem commit conhecido


# -- o que a tela usa -----------------------------------------------------------------------------

class AtualizacaoDeTeste:
    def __init__(self, raiz: Path | None = None,
                 despachar: Callable[[Callable[[], None]], None] | None = None,
                 buscar_commit: Callable[[], str] = buscar_commit_remoto,
                 baixar_zip: Callable[[Path, Callable[[int], None]], None] = baixar_zip_remoto,
                 buscar_tamanho: Callable[[str], int | None] = tamanho_remoto,
                 pausa: float = PAUSA_ENTRE_ETAPAS):
        self.raiz = Path(raiz) if raiz else raiz_do_app()
        self._despachar = despachar or (lambda funcao: funcao())
        self._buscar_commit = buscar_commit
        self._baixar_zip = baixar_zip
        self._buscar_tamanho = buscar_tamanho
        self._pausa = pausa
        self.momento = Momento.INATIVO
        self.commit_remoto: str | None = None
        self.tamanho_estimado: int | None = None    # sem compactar; só uma ideia antes de baixar
        self.bytes_baixados = 0
        self.tamanho_do_pacote: int | None = None   # o zip inteiro, conhecido quando termina de baixar
        self.etapa_da_instalacao = ""
        self.etapas_feitas = 0
        self.thread: threading.Thread | None = None
        self._ouvintes: list[Callable[[], None]] = []
        self._ouvintes_do_progresso: list[Callable[[], None]] = []

    @property
    def habilitada(self) -> bool:
        return pode_atualizar(self.raiz)

    @property
    def ocupada(self) -> bool:
        return self.momento in (Momento.PROCURANDO, Momento.BAIXANDO, Momento.INSTALANDO)

    @property
    def commit_atual(self) -> str | None:
        return commit_instalado(self.raiz)

    @property
    def tem_versao_anterior(self) -> bool:
        return tem_versao_anterior(self.raiz)

    def ao_mudar(self, funcao: Callable[[], None]) -> None:
        self._ouvintes.append(funcao)

    def ao_progredir(self, funcao: Callable[[], None]) -> None:
        """Quem quer saber de cada avanço do download e da instalação, sem trocar de momento."""
        self._ouvintes_do_progresso.append(funcao)

    def tirar_ouvinte_do_progresso(self, funcao: Callable[[], None]) -> None:
        if funcao in self._ouvintes_do_progresso:
            self._ouvintes_do_progresso.remove(funcao)

    def _progrediu(self) -> None:
        for funcao in list(self._ouvintes_do_progresso):
            funcao()

    def _mudar(self, momento: Momento) -> None:
        self.momento = momento
        for funcao in list(self._ouvintes):
            funcao()

    def frase(self) -> str:
        return FRASES[self.momento]

    def versao_em_texto(self) -> str:
        atual = self.commit_atual
        texto = f"Versão instalada: {atual[:7]}" if atual else "Versão instalada: desconhecida"
        if self.commit_remoto and self.momento == Momento.HA_NOVA:
            texto += f". Nova: {self.commit_remoto[:7]}"
        return texto

    # -- ações (cada uma roda numa thread; a tela é avisada pela thread principal) ------------

    def verificar(self, silenciosa: bool = False) -> None:
        if self.ocupada or not self.habilitada:
            return
        self._mudar(Momento.PROCURANDO)
        self._iniciar(self._procurar, silenciosa)

    def instalar(self) -> None:
        if self.momento != Momento.HA_NOVA or self.commit_remoto is None:
            return
        self.bytes_baixados, self.tamanho_do_pacote = 0, None
        self.etapa_da_instalacao, self.etapas_feitas = "", 0
        self._mudar(Momento.BAIXANDO)
        self._iniciar(self._baixar_e_trocar)

    def _iniciar(self, alvo, *args) -> None:
        self.thread = threading.Thread(target=alvo, args=args, name="atualizacao-de-teste",
                                       daemon=True)
        self.thread.start()

    def _procurar(self, silenciosa: bool) -> None:
        try:
            remoto = self._buscar_commit()
            igual = remoto == self.commit_atual
            resultado = Momento.ATUALIZADO if igual else Momento.HA_NOVA
            tamanho = None if igual else self._buscar_tamanho(remoto)
        except Exception:
            log.exception("não consegui procurar atualização")
            remoto, tamanho, resultado = None, None, Momento.INATIVO if silenciosa else Momento.FALHOU

        def concluir() -> None:
            self.commit_remoto = remoto
            self.tamanho_estimado = tamanho
            self._mudar(resultado)
        self._despachar(concluir)

    def _baixar_e_trocar(self) -> None:
        resultado = Momento.PRONTO
        try:
            with tempfile.TemporaryDirectory(dir=self.raiz) as pasta:
                arquivo = Path(pasta) / "dev.zip"
                self._baixar_zip(arquivo, self._ao_baixar)
                tamanho = arquivo.stat().st_size

                def terminou_de_baixar() -> None:
                    self.bytes_baixados = self.tamanho_do_pacote = tamanho
                    self._mudar(Momento.INSTALANDO)
                self._despachar(terminou_de_baixar)
                time.sleep(self._pausa)
                instalar_zip(arquivo, self.raiz, self.commit_remoto, self._ao_etapa)
                time.sleep(self._pausa)
        except Exception:
            log.exception("não consegui instalar a atualização")
            resultado = Momento.FALHOU
        self._despachar(lambda: self._mudar(resultado))

    def _ao_baixar(self, bytes_baixados: int) -> None:
        """Chamado na thread do download: leva o andamento à tela."""
        def atualizar() -> None:
            self.bytes_baixados = bytes_baixados
            self._progrediu()
        self._despachar(atualizar)

    def _ao_etapa(self, texto: str) -> None:
        """Chamado na thread da instalação a cada passo; cada um fica visível um instante."""
        def atualizar() -> None:
            self.etapa_da_instalacao = texto
            self.etapas_feitas += 1
            self._progrediu()
        self._despachar(atualizar)
        time.sleep(self._pausa)

    # -- o que a tela conta sobre o andamento -----------------------------------------------------

    def tamanho_em_texto(self) -> str:
        """O tamanho da atualização, do jeito mais exato que se sabe em cada momento."""
        if self.momento == Momento.BAIXANDO:
            return f"Baixado até agora: {formatar_bytes(self.bytes_baixados)}"
        if self.momento in (Momento.INSTALANDO, Momento.PRONTO) and self.tamanho_do_pacote:
            return f"Tamanho da atualização: {formatar_bytes(self.tamanho_do_pacote)}"
        if self.momento == Momento.HA_NOVA and self.tamanho_estimado:
            return f"Tamanho aproximado: {formatar_bytes(self.tamanho_estimado)} (descompactado)"
        return ""

    def etapas(self) -> list[tuple[str, str]]:
        """As três etapas com a marca de cada uma: ("✓" feita, "→" em andamento, "○" ainda não)."""
        m = self.momento
        baixou = m in (Momento.INSTALANDO, Momento.PRONTO)
        if m == Momento.BAIXANDO:
            baixar = ("→", f"Baixando a atualização: {formatar_bytes(self.bytes_baixados)}")
        elif baixou:
            baixar = ("✓", f"Atualização baixada ({formatar_bytes(self.tamanho_do_pacote)})")
        else:
            baixar = ("○", "Baixar a atualização")
        if m == Momento.INSTALANDO:
            detalhe = f": {self.etapa_da_instalacao}" if self.etapa_da_instalacao else ""
            instalar = ("→", f"Instalando a versão nova{detalhe}")
        elif m == Momento.PRONTO:
            instalar = ("✓", "Versão nova instalada")
        else:
            instalar = ("○", "Instalar a versão nova")
        reiniciar = (("→", "Reinicie o aplicativo para usar a versão nova") if m == Momento.PRONTO
                     else ("○", "Reiniciar o aplicativo"))
        return [baixar, instalar, reiniciar]

    def fracao(self) -> float | None:
        """Quanto da instalação já andou (0 a 1). None enquanto baixa (o total não é conhecido)."""
        if self.momento == Momento.PRONTO:
            return 1.0
        if self.momento == Momento.INSTALANDO:
            return min(1.0, self.etapas_feitas / ETAPAS_DA_INSTALACAO)
        return None

    def voltar_a_anterior(self) -> None:
        """Desfaz a última atualização (síncrono: é só renomear pastas)."""
        if self.ocupada:
            return
        try:
            voltar_a_versao_anterior(self.raiz)
            self._mudar(Momento.PRONTO)
        except Exception:
            log.exception("não consegui voltar à versão anterior")
            self._mudar(Momento.FALHOU)

    def preparar_reinicio(self) -> None:
        """Agenda a abertura do app de novo, daqui a 2 s (dá tempo de a janela atual fechar)."""
        comando = f"sleep 2; cd {shlex.quote(str(self.raiz))} && exec {shlex.quote(sys.executable)} -m moa"
        subprocess.Popen(["sh", "-c", comando], start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
