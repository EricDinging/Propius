#!/bin/bash

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

        if [ "$use_gpu" = "y" ]; then
            echo "===!!!Starting docker network for evaluation!!!==="    
            set -x
            sed -i "s/use_cuda: .*/use_cuda: True/" ./propius/global_config.yml
            sed -i "s/use_cuda: .*/use_cuda: True/" ./evaluation/evaluation_config.yml    
            docker compose -f compose_eval_gpu.yml up --build
            set +x
        else
            echo "===!!!Starting docker network for evaluation!!!==="
            set -x
            docker compose -f compose_eval.yml up --build
            set +x
        fi

    else
        #TODO
        echo "Better use docker, see you!"
    fi
fi