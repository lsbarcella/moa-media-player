"""Ponto de entrada: python3 -m moa"""

import sys

from moa.app import MoaApp


def main() -> int:
    app = MoaApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
