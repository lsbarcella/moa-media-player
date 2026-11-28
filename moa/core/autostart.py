# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Abertura automática com o sistema. Sem GTK.

O CLAUDE.md pede a abertura automática ligada por padrão. Na primeira execução
o app cria `~/.config/autostart/br.tcc.Moa.desktop`. Duas regras:

1. **Só uma vez.** Um marcador em `pasta_de_dados` registra que já foi feito.
   Se o usuário apagar o atalho (para desligar a abertura automática), o app
   não o recria: a escolha dele vale.
2. **Só quando o app está instalado.** O atalho precisa de um comando que
   funcione de qualquer pasta (`moa`, que o pacote .deb instala). Rodando a
   partir do código-fonte (`python3 -m moa`, em desenvolvimento) nada é criado,
   para o ambiente de desenvolvimento não ganhar um autostart sem querer.
"""

import logging
import shutil
from pathlib import Path

log = logging.getLogger(__name__)

NOME_DO_ATALHO = "br.tcc.Moa.desktop"
NOME_DO_MARCADOR = "autostart-criado"
COMANDO = "moa"

MODELO = """[Desktop Entry]
Type=Application
Name=Moa Media Player
Comment=Ouvir sua coleção de discos
Exec={exec}
Icon=br.tcc.Moa
Terminal=false
X-GNOME-Autostart-enabled=true
"""


def garantir(pasta_de_config: Path, pasta_de_dados: Path, comando: str | None = None) -> bool:
    """Cria o atalho de abertura automática na primeira execução. Devolve True se criou.

    `comando` é o caminho do executável; por padrão procura `moa` no PATH.
    Qualquer falha vai para o log e o app segue normalmente.
    """
    marcador = Path(pasta_de_dados) / NOME_DO_MARCADOR
    if marcador.exists():
        return False
    comando = comando or shutil.which(COMANDO)
    if comando is None:
        log.info("abertura automática: o comando %r não está instalado, nada a fazer", COMANDO)
        return False
    atalho = Path(pasta_de_config) / "autostart" / NOME_DO_ATALHO
    try:
        atalho.parent.mkdir(parents=True, exist_ok=True)
        if not atalho.exists():
            atalho.write_text(MODELO.format(exec=comando), encoding="utf-8")
        marcador.parent.mkdir(parents=True, exist_ok=True)
        marcador.write_text("1\n", encoding="utf-8")
    except OSError as erro:
        log.warning("não consegui ligar a abertura automática: %s", erro)
        return False
    log.info("abertura automática ligada em %s", atalho)
    return True
