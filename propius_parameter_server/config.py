"""Propius parameter server system configuration."""

import pathlib

PROPIUS_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROPIUS_PARAMETER_SERVER_ROOT = pathlib.Path(__file__).resolve().parent
GLOBAL_CONFIG_FILE = PROPIUS_ROOT / "global_config.yml"
