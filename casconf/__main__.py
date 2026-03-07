"""Entry point for ``python -m casconf``."""

from __future__ import annotations

import sys

from casconf.cli import main

if __name__ == "__main__":
    sys.exit(main())
