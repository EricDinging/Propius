"""Propius parameter server system configuration."""

import pathlib

PROPIUS_PARAMETER_SERVER_ROOT = pathlib.Path(__file__).resolve().parent
GLOBAL_CONFIG_FILE = PROPIUS_PARAMETER_SERVER_ROOT / "global_config.yml"
