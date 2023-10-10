#!/bin/bash
set -Eeuo pipefail

echo "Initialize Propius evaluation environment..."

read -p "Have you finished setting in propius/global_config.yml and evaluation/evaluation_config.yml?(y/n): " do_setting
if [ "$do_setting" != "y" ]; then
    #TODO
    echo "Make changes to these files first!"
fi
        
chmod +x evaluation/executor/entrypoint.sh
chmod +x propius/client_manager/entrypoint.sh
chmod +x evaluation/job/entrypoint.sh
chmod +x evaluation/client/entrypoint.sh


docker compose -f compose_eval_gpu.yml up --build -d