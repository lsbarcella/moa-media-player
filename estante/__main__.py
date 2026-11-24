"""Ponto de entrada: python3 -m estante"""

import sys

from estante.app import EstanteApp


def main() -> int:
    app = EstanteApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
