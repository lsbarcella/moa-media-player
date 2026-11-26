# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Leonardo dos Santos Barcella
# Este arquivo faz parte do Moa Media Player. Veja o arquivo LICENSE na raiz do projeto.

"""Ponto de entrada: python3 -m moa"""

import sys

from moa.app import MoaApp


def main() -> int:
    app = MoaApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
