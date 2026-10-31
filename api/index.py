"""Vercel Python function entrypoint: serves the FastAPI app for every /api/* route.

vercel.json rewrites /api/(.*) here; the static frontend is served by Vercel's CDN.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402

__all__ = ["app"]
