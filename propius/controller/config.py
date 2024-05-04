"""Propius Controller system configuration."""

import pathlib

# PROPIUS_ROOT = pathlib.Path(__file__).resolve().parent.parent
# PROPIUS_CONTROLLER_ROOT = pathlib.Path(__file__).resolve().parent
PROPIUS_ROOT = pathlib.Path("/var/locally-mounted/Propius/propius")
PROPIUS_CONTROLLER_ROOT = pathlib.Path("/var/locally-mounted/Propius/propius/controller")
GLOBAL_CONFIG_FILE = PROPIUS_ROOT / "global_config.yml"