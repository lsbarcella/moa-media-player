#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Mede o desempenho do Moa de forma repetível e grava um CSV (ADR-0021).

Uso (de qualquer pasta):  bash tools/measure.sh [--rapido] [--sem-audio] [--saida PASTA]

O que mede, em duas coleções sintéticas (nada da música de verdade é tocado nem lido):
- `mix`:     UM disco com 371 faixas, como a coleção do usuário;
- `estante`: 80 discos de 10 faixas, como o acervo descrito no CLAUDE.md.

1. Abertura (processo de verdade, janela de verdade): tempo até a estante aparecer, sem o
   cache do app (`abertura_1a_ms`) e com ele (`abertura_seguinte_ms`); RAM e CPU em repouso.
2. Ações (dentro deste processo, com a janela desenhada fora da tela): quanto cada clique
   leva até a tela estar pronta (abrir disco, tocar/pausar, próxima, volume...).
3. CPU tocando (som de verdade, 10 s): precisa de placa de som; `--sem-audio` pula.

O CSV tem uma linha por medida e a configuração da máquina em cada linha (CPU, RAM, tipo
de disco, sistema, Python, GTK, versão do app). Sem nome da máquina nem do usuário.

Para o autor (vem de TypeScript): é um script de benchmark. A parte 1 abre o app como um
processo filho e lê o log dele; as partes 2 e 3 importam o app e o cronometram por dentro.
"""

import argparse
import csv
import os
import platform
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

METAS = {                    # CLAUDE.md, seção 10 (a RAM é comparada com o Rhythmbox, à mão)
    "abertura_1a_ms": ("<=", 3000),
    "abertura_seguinte_ms": ("<=", 1000),
    "cpu_tocando_pct": ("<", 5),
}
REPETICOES = 5
ESPERA_DO_REPOUSO = 3.0
SEGUNDOS_TOCANDO = 10.0
TEMPO_MAXIMO_DE_ABERTURA = 120.0
MARCADOR = "estante pronta"
SEGUNDOS_ENTRE_BATIMENTOS = 5.0
LIMITE_DA_TELA_PRONTA = 5.0


# ---------------------------------------------------------------------------
# O que aparece na tela
# ---------------------------------------------------------------------------

class Console:
    """Escreve na tela e no arquivo de log, com a hora desde o começo, e avisa que está vivo.

    Quando um passo demora e nada novo aparece por 5 s, uma linha "ainda trabalhando" mostra que
    o script não travou. Tudo o que aparece na tela também vai para o `.log` (para me mandar).
    """

    def __init__(self) -> None:
        self.inicio = time.monotonic()
        self._ultimo = self.inicio
        self.passo = ""          # o que o aviso "ainda trabalhando" diz que está rodando
        self.base = ""
        self.arquivo = None
        self._trava = threading.Lock()
        self._parar = threading.Event()

    def abrir_log(self, caminho: Path) -> None:
        self.arquivo = open(caminho, "a", encoding="utf-8")

    def tempo(self) -> str:
        total = int(time.monotonic() - self.inicio)
        return f"{total // 60:02d}:{total % 60:02d}"

    def dizer(self, texto: str = "", *, erro: bool = False) -> None:
        with self._trava:
            linha = f"[{self.tempo()}] {texto}" if texto else ""
            print(linha, file=sys.stderr if erro else sys.stdout, flush=True)
            if self.arquivo:
                self.arquivo.write(linha + "\n")
                self.arquivo.flush()
            self._ultimo = time.monotonic()

    def novo_passo(self, numero: int, total: int, texto: str) -> None:
        self.passo = self.base = texto
        self.dizer(f"({numero}/{total}) {texto}")

    def batimento(self) -> None:
        """Roda numa thread: de tempos em tempos diz que ainda está trabalhando."""
        while not self._parar.wait(0.2):
            parado = time.monotonic() - self._ultimo
            if parado >= SEGUNDOS_ENTRE_BATIMENTOS:
                self.dizer(f"   ... ainda trabalhando ({self.passo}); sem novidade há {parado:.0f} s")

    def iniciar_batimento(self) -> None:
        threading.Thread(target=self.batimento, daemon=True).start()

    def parar(self) -> None:
        self._parar.set()
        if self.arquivo:
            self.arquivo.close()


console = Console()


def esperar(segundos: float, motivo: str) -> None:
    """Dorme `segundos` dizendo por quê (um sleep mudo parece travamento)."""
    console.dizer(f"   aguardando {segundos:.0f} s ({motivo})")
    time.sleep(segundos)


# ---------------------------------------------------------------------------
# A máquina
# ---------------------------------------------------------------------------

def _ler(caminho: str) -> str:
    try:
        return Path(caminho).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _tipo_de_disco() -> str:
    """HDD se algum disco real for mecânico, SSD se nenhum for, desconhecido se não der para saber."""
    tipos = set()
    for pasta in Path("/sys/block").glob("*"):
        if pasta.name.startswith(("loop", "ram", "sr", "zram", "dm-", "md", "nbd")):
            continue
        valor = _ler(str(pasta / "queue" / "rotational")).strip()
        if valor in ("0", "1"):
            tipos.add("HDD" if valor == "1" else "SSD")
    if not tipos:
        return "desconhecido"
    return "+".join(sorted(tipos))


def descrever_a_maquina() -> dict[str, str]:
    cpu = next((l.split(":", 1)[1].strip() for l in _ler("/proc/cpuinfo").splitlines()
                if l.startswith("model name")), "desconhecida")
    memoria = next((int(l.split()[1]) // 1024 for l in _ler("/proc/meminfo").splitlines()
                    if l.startswith("MemTotal")), 0)
    so = next((l.split("=", 1)[1].strip().strip('"') for l in _ler("/etc/os-release").splitlines()
               if l.startswith("PRETTY_NAME")), platform.system())
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
        gtk = f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
    except Exception:
        gtk = "desconhecido"
    try:
        from moa.core.atualizacao_de_teste import commit_instalado
        commit = (commit_instalado(RAIZ) or "desconhecido")[:7]
    except Exception:
        commit = "desconhecido"
    return {
        "cpu": cpu, "nucleos": str(os.cpu_count() or 0), "ram_mb": str(memoria),
        "disco": _tipo_de_disco(), "so": so,
        "desktop": os.environ.get("XDG_CURRENT_DESKTOP", "desconhecido"),
        "python": platform.python_version(), "gtk": gtk, "commit": commit,
    }


# ---------------------------------------------------------------------------
# A coleção de teste
# ---------------------------------------------------------------------------

def _gerar_audio(destino: Path, buffers: int) -> bool:
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst
    Gst.init(None)
    codificador = {".mp3": "lamemp3enc", ".flac": "flacenc"}[destino.suffix]
    if Gst.ElementFactory.find(codificador) is None:
        return False
    pipeline = Gst.parse_launch(
        f"audiotestsrc num-buffers={buffers} samplesperbuffer=1024 wave=sine ! audioconvert ! "
        f'audioresample ! {codificador} ! filesink location="{destino}"')
    pipeline.set_state(Gst.State.PLAYING)
    mensagem = pipeline.get_bus().timed_pop_filtered(
        120 * Gst.SECOND, Gst.MessageType.EOS | Gst.MessageType.ERROR)
    pipeline.set_state(Gst.State.NULL)
    return mensagem is not None and mensagem.type == Gst.MessageType.EOS


def gerar_audio_base(pasta: Path, buffers: int, nome: str) -> Path:
    """MP3 se o codificador existir (é o formato do acervo); senão FLAC (vem no plugins-good)."""
    for extensao in (".mp3", ".flac"):
        destino = pasta / f"{nome}{extensao}"
        if _gerar_audio(destino, buffers):
            return destino
    raise RuntimeError("não consegui gerar áudio de teste (faltam lamemp3enc e flacenc)")


def _etiquetar(arquivo: Path, **tags: str) -> None:
    import mutagen
    m = mutagen.File(arquivo, easy=True)
    if m is None:
        return
    if m.tags is None:
        m.add_tags()
    for chave, valor in tags.items():
        m[chave] = valor
    m.save()


def gerar_colecao(destino: Path, base: Path, discos: int, faixas: int, artista: str) -> int:
    """`discos` pastas com `faixas` cópias do áudio base, cada uma com tags completas."""
    for d in range(1, discos + 1):
        pasta = destino / f"{artista} {d:03d}"
        pasta.mkdir(parents=True)
        for f in range(1, faixas + 1):
            arquivo = pasta / f"{f:03d}{base.suffix}"
            shutil.copyfile(base, arquivo)
            _etiquetar(arquivo, title=f"Música {d}-{f}", album=f"Disco {d}", artist=artista,
                       albumartist=artista, tracknumber=str(f))
    return discos * faixas


def gerar_colecao_longa(destino: Path, longa: Path, discos: int, faixas: int) -> None:
    """Como `gerar_colecao`, mas cada faixa é um link para UM áudio longo, sem tags.

    Serve para medir as ações: com faixas curtas o disco avançaria sozinho o tempo todo e a tela
    nunca ficaria parada. Sem tags, a biblioteca cai nos fallbacks (nome da pasta e do arquivo).
    """
    for d in range(1, discos + 1):
        pasta = destino / f"Disco {d:03d}"
        pasta.mkdir(parents=True)
        for f in range(1, faixas + 1):
            os.symlink(longa, pasta / f"{f:03d}{longa.suffix}")


def montar_cenarios(pasta: Path, rapido: bool) -> tuple[dict[str, Path], dict[str, Path]]:
    """Devolve (coleções para abrir o app, coleções para cronometrar as ações)."""
    console.dizer("   gerando o áudio de teste curto...")
    base = gerar_audio_base(pasta, buffers=8, nome="base")
    console.dizer("   gerando o áudio de teste de 5 minutos...")
    longa = gerar_audio_base(pasta, buffers=int(300 * 44100 / 1024), nome="longa")     # 5 minutos
    mix = (1, 20) if rapido else (1, 371)
    estante = (6, 3) if rapido else (80, 10)
    abertura, acoes = {}, {}
    for nome, (discos, faixas) in (("mix", mix), ("estante", estante)):
        console.dizer(f"   montando a coleção '{nome}': {discos} disco(s) x {faixas} faixas...")
        raiz = pasta / nome / "musica"
        raiz.mkdir(parents=True)
        gerar_colecao(raiz, base, discos, faixas, "Artista")
        abertura[nome] = raiz
        raiz_longa = pasta / nome / "musica_longa"
        raiz_longa.mkdir(parents=True)
        gerar_colecao_longa(raiz_longa, longa, discos, faixas)
        acoes[nome] = raiz_longa
    return abertura, acoes


# ---------------------------------------------------------------------------
# Parte 1: abrir o app de verdade
# ---------------------------------------------------------------------------

def _achar_o_processo(marca: str) -> int | None:
    """O PID do `python -m moa`, achado pela variável de ambiente que só ele tem."""
    for pasta in Path("/proc").glob("[0-9]*"):
        try:
            if f"MOA_MEDICAO={marca}".encode() not in (pasta / "environ").read_bytes().split(b"\0"):
                continue
            argumentos = (pasta / "cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if b"-m" in argumentos and b"moa" in argumentos:
            return int(pasta.name)
    return None


def moa_ja_aberto() -> bool:
    """Há outro Moa rodando? Ele atenderia o pedido do nosso (instância única) e estragaria a medida.

    Não dá para isolar o D-Bus: numa sessão nova o GTK espera ~25 s por serviços que não existem.
    """
    for pasta in Path("/proc").glob("[0-9]*"):
        if int(pasta.name) == os.getpid():
            continue
        try:
            argumentos = (pasta / "cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if b"-m" in argumentos and b"moa" in argumentos:
            return True
    return False


def _ticks(pid: int) -> int:
    campos = _ler(f"/proc/{pid}/stat").rsplit(")", 1)[1].split()
    return int(campos[11]) + int(campos[12])        # utime + stime


def _rss_mb(pid: int) -> float:
    for linha in _ler(f"/proc/{pid}/status").splitlines():
        if linha.startswith("VmRSS"):
            return int(linha.split()[1]) / 1024
    return 0.0


def _hora_do_log(linha: str) -> float:
    return datetime.strptime(linha[:23], "%Y-%m-%d %H:%M:%S,%f").timestamp()


def abrir_o_app(musica: Path, dados: Path, rotulo: str = "") -> tuple[float, float, float]:
    """Abre o app, espera a estante e devolve (ms até a estante, RAM em MB, CPU % em repouso)."""
    marca = uuid.uuid4().hex
    ambiente = dict(os.environ, MOA_PASTA_DE_MUSICA=str(musica), MOA_SEM_REDE="1",
                    XDG_DATA_HOME=str(dados / "dados"), XDG_CONFIG_HOME=str(dados / "config"),
                    MOA_MEDICAO=marca, PYTHONPATH=str(RAIZ))
    comando = [sys.executable, "-m", "moa"]
    log = dados / "dados" / "moa" / "moa.log"
    log.unlink(missing_ok=True)                      # só vale o que esta abertura escrever
    console.dizer(f"   abrindo o app ({rotulo}); aguardando a estante aparecer...")
    inicio = time.time()
    processo = subprocess.Popen(comando, cwd=RAIZ, env=ambiente, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        pronta = None
        while time.time() - inicio < TEMPO_MAXIMO_DE_ABERTURA and pronta is None:
            time.sleep(0.02)
            for linha in _ler(str(log)).splitlines():
                if MARCADOR in linha:
                    pronta = _hora_do_log(linha)
                    break
            if processo.poll() is not None and pronta is None:
                raise RuntimeError("o app fechou antes de mostrar a estante")
        if pronta is None:
            raise RuntimeError("a estante não apareceu a tempo")
        console.dizer(f"   a estante apareceu em {(pronta - inicio) * 1000:.0f} ms")
        esperar(ESPERA_DO_REPOUSO, "app em repouso, antes de medir a RAM")
        pid = _achar_o_processo(marca)
        if pid is None:
            raise RuntimeError("não achei o processo do app")
        antes, t0 = _ticks(pid), time.time()
        esperar(ESPERA_DO_REPOUSO, "medindo a CPU em repouso")
        cpu = (_ticks(pid) - antes) / os.sysconf("SC_CLK_TCK") / (time.time() - t0) * 100
        return (pronta - inicio) * 1000, _rss_mb(pid), cpu
    finally:
        try:
            os.killpg(processo.pid, signal.SIGTERM)
            processo.wait(timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            os.killpg(processo.pid, signal.SIGKILL)


def medir_abertura(nome: str, musica: Path, pasta: Path, frio: bool) -> list[tuple]:
    dados = pasta / nome / "app"
    if frio:
        subprocess.run(["sudo", "-n", "sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches"],
                       capture_output=True)
    primeira, _, _ = abrir_o_app(musica, dados, "1ª vez, sem o cache do app")
    seguinte, ram, cpu = abrir_o_app(musica, dados, "2ª vez, com o cache do app")
    return [(nome, "abertura_1a_ms", primeira, "ms"), (nome, "abertura_seguinte_ms", seguinte, "ms"),
            (nome, "ram_repouso_mb", ram, "MB"), (nome, "cpu_repouso_pct", cpu, "%")]


# ---------------------------------------------------------------------------
# Parte 2: as ações, por dentro
# ---------------------------------------------------------------------------

def medir_acoes(nome: str, musica: Path, pasta: Path, repeticoes: int) -> list[tuple]:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gst", "1.0")
    from gi.repository import GLib, Gst, Gtk
    from moa.core.config import Preferencias
    from moa.core.contexto import Contexto
    from moa.core.db import Database
    from moa.core.library import scan
    from moa.core.session import Tela
    from moa.ui import theme
    from moa.ui.window import Conteudo

    def sem_som() -> Gst.Element:
        destino = Gst.ElementFactory.make("fakesink", None)
        destino.set_property("sync", True)              # no ritmo normal, sem usar placa de som
        return destino

    dados = pasta / nome / "acoes"
    dados.mkdir(parents=True, exist_ok=True)
    prefs = Preferencias(dados / "config.json")
    theme.aplicar(prefs.config.paleta, prefs.config.letra)
    ctx = Contexto(Database(dados / "moa.db"), prefs, musica, sink_factory=sem_som,
                   pasta_miniaturas=dados / "miniaturas")
    conteudo = Conteudo(ctx)
    janela = Gtk.OffscreenWindow()
    janela.set_size_request(1100, 760)
    janela.add(conteudo.raiz)
    janela.show_all()
    ctx.definir_colecao(scan(musica), {})
    laco = GLib.MainContext.default()

    def pronto() -> None:
        """Deixa o GTK terminar tudo o que a ação pediu e desenha de verdade.

        Tem limite de 5 s: se a tela nunca ficar parada, a medida sai como 5000 ms em vez de
        a medição ficar presa para sempre.
        """
        limite = time.perf_counter() + LIMITE_DA_TELA_PRONTA
        while laco.iteration(False):
            if time.perf_counter() > limite:
                console.dizer("   (a tela não ficou parada em 5 s)")
                break
        janela.get_pixbuf()

    def cronometrar(rotulo: str, acao, preparo=None) -> tuple:
        """Duas medidas por ação: até a tela responder (a que o usuário sente) e até terminar de
        montar tudo (listas grandes vêm em pedaços, então o resto aparece um pouco depois)."""
        primeiras, completas = [], []
        console.passo = f"{console.base}: {rotulo}"
        for _ in range(repeticoes):
            if preparo is not None:
                preparo()
                pronto()
            t = time.perf_counter()
            acao()
            janela.get_pixbuf()                        # desenha o que já está pronto
            primeiras.append((time.perf_counter() - t) * 1000)
            pronto()
            completas.append((time.perf_counter() - t) * 1000)
        mediana, completa = statistics.median(primeiras), statistics.median(completas)
        console.dizer(f"   {rotulo:24s} {mediana:7.0f} ms  (máx {max(primeiras):.0f}; completo {completa:.0f})")
        return (nome, f"acao_{rotulo}_mediana_ms", mediana, "ms"), \
               (nome, f"acao_{rotulo}_maximo_ms", max(primeiras), "ms"), \
               (nome, f"acao_{rotulo}_completo_ms", completa, "ms")

    estante = ctx.session.voltar_para_a_estante
    disco = ctx.discos[0]
    sessao, radio = ctx.session, ctx.radio
    alterna = {"mais": True}

    def volume() -> None:
        (radio.volume_mais if alterna["mais"] else radio.volume_menos)()
        alterna["mais"] = not alterna["mais"]

    def abrir_radio() -> None:
        radio.abrir_disco(disco)
        sessao.ir_para(Tela.RADIO)

    resultados: list[tuple] = []
    console.dizer("   carregando a coleção e a janela...")
    for rotulo, acao, preparo in (
        ("abrir_disco", abrir_radio, estante),
        ("tocar_pausar", radio.alternar, None),
        ("proxima", radio.proxima, None),
        ("tocar_faixa_do_meio", lambda: radio.tocar_faixa(len(disco.tracks) // 2), None),
        ("volume", volume, None),
        ("voz_mais_clara", radio.alternar_voz_mais_clara, None),
        ("ir_para_estante", estante, abrir_radio),
        ("criar_playlist", lambda: (ctx.novo_rascunho(), sessao.ir_para(Tela.PLAYLIST)), estante),
        ("abrir_caixa", lambda: sessao.ir_para(Tela.CAIXA), estante),
        ("abrir_aparelho_de_cd", lambda: sessao.ir_para(Tela.APARELHO_DE_CD), estante),
        ("abrir_configuracoes", lambda: sessao.ir_para(Tela.CONFIGURACOES), estante),
    ):
        if rotulo in ("tocar_pausar", "proxima", "tocar_faixa_do_meio", "volume", "voz_mais_clara"):
            abrir_radio()
            pronto()
        resultados.extend(cronometrar(rotulo, acao, preparo))
    ctx.encerrar()
    ctx.banco.close()
    janela.remove(conteudo.raiz)
    janela.destroy()
    return resultados


# ---------------------------------------------------------------------------
# Parte 3: CPU tocando de verdade
# ---------------------------------------------------------------------------

def medir_cpu_tocando(pasta: Path, segundos: float) -> list[tuple]:
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import GLib
    from moa.core.config import Preferencias
    from moa.core.contexto import Contexto
    from moa.core.db import Database
    from moa.core.library import scan
    from moa.core.player import Estado

    musica = pasta / "cpu" / "musica" / "Disco"
    musica.mkdir(parents=True)
    longa = gerar_audio_base(musica, buffers=int((segundos + 15) * 44100 / 1024), nome="longa")
    ctx = Contexto(Database(pasta / "cpu" / "moa.db"), Preferencias(pasta / "cpu" / "config.json"),
                   musica.parent, pasta_miniaturas=pasta / "cpu" / "miniaturas")
    try:
        ctx.definir_colecao(scan(musica.parent), {})
        ctx.radio.abrir_disco(ctx.discos[0])
        laco = GLib.MainContext.default()
        fim = time.time() + 3
        while time.time() < fim:                       # espera começar a tocar de verdade
            laco.iteration(False)
            time.sleep(0.01)
        if ctx.player.estado != Estado.TOCANDO:
            console.dizer("   (sem som: placa de som indisponível; pulei a CPU tocando)")
            return []
        # Um laço de eventos de verdade (como o do app), não uma espera ocupada: esta medindo o
        # app tocando, não o nosso cronômetro.
        console.dizer(f"   tocando por {segundos:.0f} s e medindo a CPU...")
        principal = GLib.MainLoop()
        GLib.timeout_add(int(segundos * 1000), principal.quit)
        cpu0, t0 = time.process_time(), time.time()
        principal.run()
        cpu = (time.process_time() - cpu0) / (time.time() - t0) * 100
        return [("tocando", f"cpu_tocando_pct", cpu, "%"),
                ("tocando", "formato", 1.0 if longa.suffix == ".mp3" else 0.0, "1=mp3 0=flac")]
    finally:
        ctx.encerrar()
        ctx.banco.close()


# ---------------------------------------------------------------------------
# Saída
# ---------------------------------------------------------------------------

def avaliar(metrica: str, valor: float) -> str:
    meta = METAS.get(metrica)
    if meta is None:
        return ""
    operador, limite = meta
    passou = valor <= limite if operador == "<=" else valor < limite
    return f"{'OK  ' if passou else 'ACIMA'} (meta {operador} {limite})"


def gravar(arquivo: Path, maquina: dict[str, str], medidas: list[tuple]) -> None:
    data = datetime.now().isoformat(timespec="seconds")
    with open(arquivo, "w", newline="", encoding="utf-8") as saida:
        escritor = csv.writer(saida)
        escritor.writerow(["data", *maquina, "cenario", "metrica", "valor", "unidade"])
        for cenario, metrica, valor, unidade in medidas:
            escritor.writerow([data, *maquina.values(), cenario, metrica, f"{valor:.2f}", unidade])


def relatorio(maquina: dict[str, str], medidas: list[tuple], falhas: list[str], duracao_s: float) -> str:
    """O texto curto para colar numa conversa: máquina, abertura, ações lado a lado e falhas."""
    linhas = [f"Medição do Moa em {datetime.now():%d/%m/%Y %H:%M}, duração {int(duracao_s) // 60} min {int(duracao_s) % 60} s",
              f"Máquina: {maquina['cpu']} ({maquina['nucleos']} núcleos), {maquina['ram_mb']} MB de RAM, disco {maquina['disco']}",
              f"Sistema: {maquina['so']} | {maquina['desktop']} | Python {maquina['python']} | GTK {maquina['gtk']} | app {maquina['commit']}",
              ""]
    por_cenario: dict[str, dict[str, float]] = {}
    for cenario, metrica, valor, _unidade in medidas:
        por_cenario.setdefault(cenario, {})[metrica] = valor
    cenarios = [c for c in ("mix", "estante") if c in por_cenario]

    linhas.append("ABERTURA E REPOUSO")
    linhas.append(f"{'':26s}" + "".join(f"{c:>10s}" for c in cenarios) + "   meta")
    for metrica, rotulo in (("abertura_1a_ms", "1ª abertura (ms)"), ("abertura_seguinte_ms", "abertura seguinte (ms)"),
                            ("ram_repouso_mb", "RAM em repouso (MB)"), ("cpu_repouso_pct", "CPU em repouso (%)")):
        celulas = "".join(f"{por_cenario[c][metrica]:10.0f}" if metrica in por_cenario[c] else f"{'-':>10s}"
                          for c in cenarios)
        meta = METAS.get(metrica)
        linhas.append(f"{rotulo:26s}{celulas}" + (f"   {meta[0]} {meta[1]}" if meta else ""))

    nomes = [m[:-len("_mediana_ms")] for _c, m, _v, _u in medidas if m.endswith("_mediana_ms")]
    acoes = list(dict.fromkeys(n.removeprefix("acao_") for n in nomes))
    if acoes:
        linhas += ["", "AÇÕES (ms: até a tela responder, mediana / máximo / até terminar de montar)",
                   f"{'':26s}" + "".join(f"{c:>26s}" for c in cenarios)]
        for acao in acoes:
            celulas = ""
            for c in cenarios:
                med = por_cenario[c].get(f"acao_{acao}_mediana_ms")
                mx = por_cenario[c].get(f"acao_{acao}_maximo_ms")
                completo = por_cenario[c].get(f"acao_{acao}_completo_ms", med)
                celulas += (f"{med:8.0f} /{mx:5.0f} /{completo:6.0f}  " if med is not None
                            else f"{'-':>26s}")
            linhas.append(f"{acao:26s}{celulas}")
    if "tocando" in por_cenario and "cpu_tocando_pct" in por_cenario["tocando"]:
        linhas += ["", f"CPU tocando: {por_cenario['tocando']['cpu_tocando_pct']:.1f} % (meta < 5)"]
    if falhas:
        linhas += ["", "FALHAS (o resto da medição continuou):"] + [f"  - {f}" for f in falhas]
    return "\n".join(linhas)


def main(argumentos: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analisador.add_argument("--saida", type=Path, default=RAIZ / "medicoes")
    analisador.add_argument("--rapido", action="store_true", help="coleção pequena e 2 repetições (teste do script)")
    analisador.add_argument("--sem-audio", action="store_true", help="pula a medida de CPU tocando")
    analisador.add_argument("--frio", action="store_true",
                            help="esvazia o cache de arquivos do sistema antes (pede sudo sem senha)")
    args = analisador.parse_args(argumentos)

    if moa_ja_aberto():
        print("O Moa está aberto. Feche-o (pelo X) e rode de novo: ele atenderia o pedido da "
              "medição e estragaria os números.", file=sys.stderr)
        return 1
    args.saida.mkdir(parents=True, exist_ok=True)
    nome_base = f"medicao_{datetime.now():%Y%m%d-%H%M%S}"
    console.abrir_log(args.saida / f"{nome_base}.log")
    console.iniciar_batimento()

    maquina = descrever_a_maquina()
    console.dizer("Máquina: " + " | ".join(f"{k}={v}" for k, v in maquina.items()))
    console.dizer("Não use o computador até terminar: isso mudaria os números. "
                  "Janelas do app vão abrir e fechar sozinhas.")
    repeticoes = 2 if args.rapido else REPETICOES
    medidas: list[tuple] = []
    falhas: list[str] = []
    passos_finais = 0 if args.sem_audio else 1
    total = 1 + 2 * 2 + passos_finais                     # coleções + (abertura e ações) x 2 + CPU
    numero = 0

    def executar(texto: str, funcao) -> list[tuple]:
        """Roda um passo. Se der erro, anota (com o detalhe no .log) e deixa o resto seguir."""
        nonlocal numero
        numero += 1
        console.novo_passo(numero, total, texto)
        try:
            return funcao() or []
        except Exception as erro:
            falhas.append(f"{texto}: {type(erro).__name__}: {erro}")
            console.dizer(f"   FALHOU: {type(erro).__name__}: {erro}  (detalhes no arquivo .log)", erro=True)
            if console.arquivo:
                console.arquivo.write(traceback.format_exc())
                console.arquivo.flush()
            return []

    with tempfile.TemporaryDirectory(prefix="moa-medicao-") as temporaria:
        pasta = Path(temporaria)
        colecoes: list = []
        executar("Gerando as coleções de teste", lambda: colecoes.append(montar_cenarios(pasta, args.rapido)))
        if colecoes:
            para_abrir, para_acoes = colecoes[0]
            for nome, musica in para_abrir.items():
                medidas += executar(f"Abertura do app, coleção '{nome}' (2 aberturas)",
                                    lambda n=nome, m=musica: medir_abertura(n, m, pasta, args.frio))
            for nome, musica in para_acoes.items():
                medidas += executar(f"Tempo das ações, coleção '{nome}' ({repeticoes} repetições cada)",
                                    lambda n=nome, m=musica: medir_acoes(n, m, pasta, repeticoes))
            if not args.sem_audio:
                medidas += executar("CPU tocando de verdade",
                                    lambda: medir_cpu_tocando(pasta, 3.0 if args.rapido else SEGUNDOS_TOCANDO))

    duracao = time.monotonic() - console.inicio
    arquivo = args.saida / f"{nome_base}.csv"
    gravar(arquivo, maquina, medidas)
    texto = relatorio(maquina, medidas, falhas, duracao)
    (args.saida / f"{nome_base}.txt").write_text(texto + "\n", encoding="utf-8")
    console.dizer()
    console.dizer(f"Pronto em {console.tempo()}. Arquivos em {args.saida}/:")
    console.dizer(f"   {nome_base}.txt  <- o resumo (é este que você me manda)")
    console.dizer(f"   {nome_base}.csv  <- todos os números; {nome_base}.log <- tudo o que apareceu aqui")
    console.dizer()
    console.dizer("=== copie daqui ===")
    console.arquivo and console.arquivo.write(texto + "\n")
    print(texto)
    print("=== até aqui ===")
    console.parar()
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
