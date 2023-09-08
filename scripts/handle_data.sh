# /bin/bash

set -Eeuo pipefail
if [ $# -eq 0 ]; then
  echo "Error: Please provide a directory name as an argument."
  exit 1
fi

set -x 
dir_name="evaluation_result/$1"
mkdir "$dir_name"
cp -r ./evaluation/monitor/* "$dir_name"

set +x