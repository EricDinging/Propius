# /bin/bash

set -Eeuo pipefail

if [ $# -eq 0 ]; then
  echo "Error: Please provide a evaluation case [ evaluation | dry ]: "
  exit 1
fi

if [ $1 = "dry" ]; then
    cp ./tests/config_dry.yml ./evaluation/evaluation_config.yml -f
else
    cp ./tests/config_evaluation.yml ./evaluation/evaluation_config.yml -f
fi