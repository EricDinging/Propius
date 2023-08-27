chmod +x evaluation/executor/entrypoint.sh
chmod +x propius/client_manager/entrypoint.sh

echo "===!!!Starting docker network for evaluation!!!==="
docker compose -f compose_propius -f compose_eval_gpu up --build