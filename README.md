# Propius
Propius is a Federated Learning (FL) resource manager, capable of efficiently scheduling devices in a multi-job setting.

## Repository Organization
```
.
├── propius/                        # Propius Python package
│   ├── client_manager/             #   - Edge device (client) interface
│   ├── job_manager/                #   - FL job interface
│   ├── load_balancer/              #   - Distributor of client traffics to client managers
│   ├── scheduler/                  #   - FL job scheduler, capable of executing various policies
│   ├── util/                       #   - Utility functions and classes
│   ├── channels/                   #   - gRPC channel source code and definitions
│   ├── database/                   #   - Redis database base interface
│   ├── propius_job/                #   - Propius job interface library
│   │   └── propius_job.py          #       - Class for Propius-job interface
│   ├── propius_client/             #   - Propius client interface library
│   │   ├── propius_client.py       #       - Class for Propius-client interface
│   │   └── propius_client_aio.py   #       - asyncio-based class for Propius-client interface
│   └── global_config.yml           #   - Configuration for Propius system
│
├── evaluation/                     # Framework for evaluating scheduling policies
│   ├── analyze/                    #   - Analysis functions for time and accuracy logs
│   ├── executor/                   #   - Executor for FL training and testing tasks using multiple GPU processes
│   ├── single_executor/            #   - Light-weight executor for FL training and testing worker using one GPU process
│   ├── client/                     #   - Dispatcher of simulated clients
│   ├── job/                        #   - Dispatcher of simulated jobs
│   └── evaluation_config.yml       #   - Configuration for evaluation
│ 
├── fedscale/                       # FedScale FL training backends for evaluation and examples
│ 
├── tests/                          # Test suites
│ 
├── examples/                       # Examples of integrating Propius
│ 
└── datasets/                       # FL datasets and client device traces
```

## Getting Started
- Quick installation (Linux / MacOS)
```bash
source install.sh # add `--cuda` if you want CUDA
pip install -e .
```
- [Step-by-step installation](./docs/getting_started/getting_started.md)

## Usage
### Quick Launch
We use docker compose to containerize components (job manager, scheduler, client manager, load balancer and Redis DB) in a docker network. The config is specified in `compose_propius.yml`.
- Edit `compose_propius.yml` and `propius/global_config.yml`. By default, the network address of load balancer (client interface) is `localhost:50002`, and the address of job manager (job interface) is `localhost:50001`
- Make sure the setup is consistent across two config files
- By default, Propius has one client manager and client database. For handling large amount of clients, we support horizontal scaling of client manager and client database. To achieve this, you need to add more client manager and database services in `compose_propius.yml`, and edit `propius/global_config.yml` accordingly
- Run docker compose
```bash
docker compose -f compose_propius.yml up --build # -d if want to run Propius in background
```
- Shut down
```bash
docker compose -f compose.yml down
```
### Manual Lanuch
Propius can be started without docker. However, for the ease of deployment, the Redis database is containerized.
- Edit `propius/global_config.yml` and `compose_redis.yml`. Make sure these two files are consistent
- Launch Redis Database in background
```bash
docker compose -f compose_redis.yml up -d
```
- Launch major components in Propius
    - Scheduler:
    ```bash
    python propius/scheduler/scheduler.py
    ```
    - Job manager:
    ```bash
    python propius/job_manager/job_manager.py
    ```
    - Client manager:
    ```bash
    python propius/client_manager/client_manager.py 0 # <id>
    ```
    - Load balancer:
    ```bash
    python propius/load_balancer/load_balancer.py
    ```
- By default, Propius has one client manager and client database. For handling large amount of clients, we support horizontal scaling of client manager and client database. To achieve this, you need to add more client manager and database services `propius/global_config.yml` and `compose_redis.yml`. Make sure the setting is consistent. You also need to start the additional client manager services manually.

## Interface
- Propius' job interface is defined in `propius_job/propius_job.py`
- Propius' client interface is defined in `propius_client/propius_client.py`
- Refer to `examples/` to get an idea how your FL job and FL client can utilize Propius

## Evaluation
For the ease of evaluation, we containerize Propius and essential peripherals for evaluation in one docker network using docker compose.
- Download Dataset
```bash
source ./datasets/download.sh
```

- Make changes to `evaluation/evaluation_config.yml`
- Generate job trace based on the previous configuration. The trace file won't be generated if it already exists
```bash
python ./evaluation/job/generator.py
```
- Edit job profile in `evaluation/job/profile/`. Make sure the number of profiles matches the number specified in the configuration file.
- Edit `propius/global_config.yml`, especially when you want to change the scheduling algorithms under evaluation
- Start docker network
```bash
source ./init.sh
```

## Testing
- Under construction

## Error Handling
- If there is an error saying that you cannot connect to docker daemon, try [this](https://stackoverflow.com/questions/48957195/how-to-fix-docker-got-permission-denied-issue)
- Check Redis server is running
    - [Install redis-cli](https://stackoverflow.com/questions/21795340/linux-install-redis-cli-only)
    ```bash
    redis-cli -h localhost -p 6379 ping
    redis-cli -h localhost -p 6380 ping
    ```

## RoadMap
- Please refer to [Project](https://github.com/users/EricDinging/projects/1) page for more information



