#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path
import sys

import uvicorn


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from openagenda_rag.settings import load_api_settings


def main() -> int:
    settings = load_api_settings()
    uvicorn.run(
        "openagenda_rag.api:app",
        app_dir=str(SRC),
        host=settings.host,
        port=settings.port,
        reload=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
