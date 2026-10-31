"""Synthetic cohort taste clusters for the admin view. Not real student data."""

import json

from . import config


def load_cohort() -> dict:
    return json.loads((config.DATA_DIR / "cohort_synthetic.json").read_text())
