echo "Starting Redis database"
docker compose -f docker/job_db.yml up -d
docker compose -f docker/client_db_0.yml up -d