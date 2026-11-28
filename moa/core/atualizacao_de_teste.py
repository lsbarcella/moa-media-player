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
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
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


class ErroDeAtualizacao(Exception):
    pass


class Momento(Enum):
    INATIVO = "inativo"
    PROCURANDO = "procurando"
    ATUALIZADO = "atualizado"       # já está na versão mais nova
    HA_NOVA = "ha_nova"
    BAIXANDO = "baixando"
    PRONTO = "pronto"               # instalada; falta reiniciar
    FALHOU = "falhou"


FRASES = {
    Momento.INATIVO: "Aqui você busca uma versão mais nova do app (só no ambiente de testes).",
    Momento.PROCURANDO: "Procurando uma versão mais nova…",
    Momento.ATUALIZADO: "Você já está com a versão mais nova.",
    Momento.HA_NOVA: "Tem uma versão mais nova do app.",
    Momento.BAIXANDO: "Baixando e instalando a versão nova. Pode esperar.",
    Momento.PRONTO: "Pronto! Para usar a versão nova, o app precisa abrir de novo.",
    Momento.FALHOU: "Não consegui atualizar agora. Tudo continua como estava.",
}


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


def baixar_zip_remoto(destino: Path) -> None:
    pedido = urllib.request.Request(URL_DO_ZIP, headers={"User-Agent": AGENTE})
    total = 0
    with urllib.request.urlopen(pedido, timeout=60) as resposta, open(destino, "wb") as saida:
        while bloco := resposta.read(64 * 1024):
            total += len(bloco)
            if total > LIMITE_DO_ZIP:
                raise ErroDeAtualizacao("o arquivo baixado é grande demais")
            saida.write(bloco)


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


def instalar_zip(arquivo_zip: Path, raiz: Path, commit: str) -> None:
    """Confere o zip e troca `moa/` (e `tools/`) pela versão nova. Se algo falhar, nada muda.

    `moa/` é o app e é obrigatório. `tools/` (medição, scripts) acompanha a `dev`, mas se a troca
    dele falhar a atualização vale mesmo assim.
    """
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
        _trocar_pasta(pacote, raiz / "moa", raiz / "moa.anterior")
        if (base / "tools").is_dir():
            try:
                _trocar_pasta(base / "tools", raiz / "tools", raiz / "tools.anterior")
            except OSError:
                log.exception("não consegui atualizar a pasta tools; o app foi atualizado mesmo assim")
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
                 baixar_zip: Callable[[Path], None] = baixar_zip_remoto):
        self.raiz = Path(raiz) if raiz else raiz_do_app()
        self._despachar = despachar or (lambda funcao: funcao())
        self._buscar_commit = buscar_commit
        self._baixar_zip = baixar_zip
        self.momento = Momento.INATIVO
        self.commit_remoto: str | None = None
        self.thread: threading.Thread | None = None
        self._ouvintes: list[Callable[[], None]] = []

    @property
    def habilitada(self) -> bool:
        return pode_atualizar(self.raiz)

    @property
    def ocupada(self) -> bool:
        return self.momento in (Momento.PROCURANDO, Momento.BAIXANDO)

    @property
    def commit_atual(self) -> str | None:
        return commit_instalado(self.raiz)

    @property
    def tem_versao_anterior(self) -> bool:
        return tem_versao_anterior(self.raiz)

    def ao_mudar(self, funcao: Callable[[], None]) -> None:
        self._ouvintes.append(funcao)

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
        except Exception:
            log.exception("não consegui procurar atualização")
            remoto, resultado = None, Momento.INATIVO if silenciosa else Momento.FALHOU

        def concluir() -> None:
            self.commit_remoto = remoto
            self._mudar(resultado)
        self._despachar(concluir)

    def _baixar_e_trocar(self) -> None:
        resultado = Momento.PRONTO
        try:
            with tempfile.TemporaryDirectory(dir=self.raiz) as pasta:
                arquivo = Path(pasta) / "dev.zip"
                self._baixar_zip(arquivo)
                instalar_zip(arquivo, self.raiz, self.commit_remoto)
        except Exception:
            log.exception("não consegui instalar a atualização")
            resultado = Momento.FALHOU
        self._despachar(lambda: self._mudar(resultado))

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
