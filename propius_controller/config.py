"""Propius Controller system configuration."""

import pathlib

PROPIUS_CONTROLLER_ROOT = pathlib.Path(__file__).resolve().parent
GLOBAL_CONFIG_FILE = PROPIUS_CONTROLLER_ROOT / "global_config.yml"
