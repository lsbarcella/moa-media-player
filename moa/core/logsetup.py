# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Log em arquivo e rede de segurança para erros inesperados. Sem GTK.

Regra do projeto (CLAUDE.md, seção 5, item 5): nada técnico chega ao idoso.
Tudo o que é técnico (erro, exceção, stack trace) vai para um arquivo que o
autor consulta fora do app. Na tela, no máximo uma frase calma.

Dois pedaços:
- `configurar_log`: liga o log em arquivo, com rotação (o arquivo não cresce
  sem limite num HD pequeno).
- `instalar_gancho_de_excecao`: se algum código lançar uma exceção que
  ninguém tratou, ela é registrada no log e o app avisa com uma frase calma,
  em vez de fechar ou de despejar um erro no terminal. Em TypeScript seria um
  `window.onerror` / `process.on("uncaughtException")`.
"""

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable

NOME_DO_ARQUIVO = "moa.log"
TAMANHO_MAXIMO = 512 * 1024      # 512 KB por arquivo
COPIAS_ANTIGAS = 3               # moa.log, moa.log.1, .2, .3 => no máximo ~2 MB
FORMATO = "%(asctime)s %(levelname)s %(name)s: %(message)s"

MSG_FALHA_INESPERADA = "Algo não saiu como eu esperava. Pode tentar de novo."


def configurar_log(pasta: Path, nivel: int = logging.INFO) -> Path | None:
    """Liga o log em `pasta/moa.log`. Devolve o caminho, ou None se não deu.

    Se a pasta não puder ser criada ou escrita, o app segue sem log em arquivo
    (um erro ao registrar erros não pode derrubar o programa).
    Chamar de novo não duplica as linhas.
    """
    raiz = logging.getLogger()
    caminho = Path(pasta) / NOME_DO_ARQUIVO
    for existente in raiz.handlers:
        if getattr(existente, "_moa", False):
            raiz.removeHandler(existente)
            existente.close()
    try:
        Path(pasta).mkdir(parents=True, exist_ok=True)
        arquivo = RotatingFileHandler(caminho, maxBytes=TAMANHO_MAXIMO,
                                      backupCount=COPIAS_ANTIGAS, encoding="utf-8")
    except OSError:
        return None
    arquivo.setFormatter(logging.Formatter(FORMATO))
    arquivo._moa = True        # marca o nosso, para achá-lo (e trocá-lo) depois
    raiz.addHandler(arquivo)
    raiz.setLevel(nivel)
    return caminho


def instalar_gancho_de_excecao(ao_falhar: Callable[[], None]) -> None:
    """Registra exceções não tratadas e chama `ao_falhar` para avisar o idoso.

    `ao_falhar` pode ser chamada de qualquer thread; quem a passa é que deve
    levá-la para a thread principal da interface, se precisar.
    """
    log = logging.getLogger("moa.falha")

    def tratar(tipo, valor, rastro) -> None:
        if issubclass(tipo, KeyboardInterrupt):
            sys.__excepthook__(tipo, valor, rastro)
            return
        log.error("exceção não tratada", exc_info=(tipo, valor, rastro))
        try:
            ao_falhar()
        except Exception:                      # o aviso em si nunca pode causar outra falha
            log.exception("falhou ao avisar sobre a exceção")

    sys.excepthook = tratar
    threading.excepthook = lambda args: tratar(args.exc_type, args.exc_value, args.exc_traceback)
