#!/bin/bash
set -Eeuo pipefail

echo "Initialize Propius evaluation environment..."

read -p "Have you finished setting in propius/global_config.yml and evaluation/evaluation_config.yml?(y/n): " do_setting
if [ "$do_setting" != "y" ]; then
    #TODO
    echo "Make changes to these files first!"
else
    read -p "Use docker?(y/n): " use_docker
    if [ "$use_docker" = "y" ]; then
        set -x
        sed -i "s/use_docker: .*/use_docker: True/" ./propius/global_config.yml
        sed -i "s/use_docker: .*/use_docker: True/" ./evaluation/evaluation_config.yml
        
        chmod +x evaluation/executor/entrypoint.sh
        chmod +x propius/client_manager/entrypoint.sh
        set +x

        read -p "Use GPU?(y/n): " use_gpu

        echo "===!!!Starting docker network for evaluation!!!==="    
        if [ "$use_gpu" = "y" ]; then
            set -x
            sed -i "s/use_cuda: .*/use_cuda: True/" ./propius/global_config.yml
            sed -i "s/use_cuda: .*/use_cuda: True/" ./evaluation/evaluation_config.yml
            set +x
            read -p "Rebuild docker network?(y/n): " rebuild
            if [ "$rebuild" = "y" ]; then
                set -x
                docker compose -f compose_eval_gpu.yml up --build
                set +x
            else
                set -x
                docker compose -f compose_eval_gpu.yml up
                set +x
            fi
        else
            set -x
            sed -i "s/use_cuda: .*/use_cuda: False/" ./propius/global_config.yml
            sed -i "s/use_cuda: .*/use_cuda: False/" ./evaluation/evaluation_config.yml
            set +x
            read -p "Rebuild docker network?(y/n): " rebuild
            if [ "$rebuild" = "y" ]; then
                set -x
                docker compose -f compose_eval.yml up --build
                set +x
            else
                set -x
                docker compose -f compose_eval.yml up
                set +x
            fi
        fi

        

    else
        #TODO
        echo "Better use docker, see you!"
    fi
fi