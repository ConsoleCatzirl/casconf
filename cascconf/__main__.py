"""Entry point for ``python -m cascconf``."""

from __future__ import annotations

import sys

from cascconf.cli import main

if __name__ == "__main__":
    sys.exit(main())
