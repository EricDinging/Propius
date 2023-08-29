# Propius
Propius is a Federated Learning resource manager, capable of efficiently schedule devices in a multi-job setting, with the goal of reducing average job completion time.

## Repository Organization
```
.
├── propius/                    # Propius Python package
│   ├── client_manager/         #   - Edge device (client) interface
│   ├── job_manager/            #   - FL job interface
│   ├── load_balancer/          #   - Distributor of client traffics to client managers
│   ├── scheduler/              #   - FL job scheduler, capable of executing various policies
│   ├── util/                   #   - Utility functions and classes
│   ├── channels/               #   - gRPC channel source code and definitions
│   ├── database/               #   - Redis database base interface
│   └── global_config.yml       #   - Configuration for Propius system
│
├── propius_client/             # Propius client interface library
│   ├── propius_client.py       #   - Class for Propius-client interface
│   └── propius_client_aio.py   #   - asyncio-based class for Propius-client interface
│
├── propius_job/                # Propius job interface library
│   └── propius_job.py          #   - Class for Propius-job interface
│
├── evaluation/                 # Framework for evaluating scheduling policies
│   ├── analyze/                #   - Analysis functions for time and accuracy logs
│   ├── executor/               #   - Distributor of FL training and testing tasks to multiple GPU processes
│   ├── single_executor/        #   - Simple version of FL training and testing worker using one GPU process
│   ├── client/                 #   - Dispatcher of simulated clients
│   ├── job/                    #   - Dispatcher of simulated jobs
│   └── evaluation_config.yml   #   - Configuration for evaluation
│ 
├── tests/                      # Test suites
│ 
├── examples/                   # Examples of integrating Propius
│ 
└── datasets/                   # FL datasets and client device traces
```

## Get Started
### Quick installation (Linux)
```bash
source install.sh # add `--cuda` if you want CUDA
pip install -e .
```

### Installation from Source (Linux/MacOS)
- If your machine has GPU and you want to use CUDA, check [this](https://askubuntu.com/questions/799184/how-can-i-install-cuda-on-ubuntu-16-04)
- Download Anaconda if not installed
```bash
wget https://repo.anaconda.com/archive/Anaconda3-2023.03-1-Linux-x86_64.sh
bash Anaconda3-2023.03-1-Linux-x86_64.sh
conda list
```
- If your device space is not enough for the entire Anaconda package, you can consider installing [miniconda](https://educe-ubc.github.io/conda.html) 
- Navigate into `Propius` package, install and activate `propius` conda environment
    - If you are using cuda
    ```bash
    cd Propius
    conda env create -f environment_cuda.yml
    conda activate propius
    conda install pytorch==1.12.1 torchvision==0.13.1 torchaudio==0.12.1 cudatoolkit=11.3 -c pytorch
    ```
    - If you are not using cuda

    ```bash
    cd Propius
    conda env create -f environment.yml
    conda activate propius
    ```
- Install docker and docker-compose
    - [docker installation guide (step 1)](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-16-04)
    - [docker compose](https://docs.docker.com/compose/install/linux/#install-the-plugin-manually)


## RoadMap
- Please refer to [Project](https://github.com/users/EricDinging/projects/1) page for more info
## Usage
### Quick Launch
We use docker compose to containerize components (job manager, scheduler, client manager, load balancer and Redis DB) in a docker network. The config is specified in `compose_propius.yml`.
- Edit `compose_propius.yml` and `propius/global_config.yml`. By default, the interfacing port of load balancer (client interface) is `50002`, and the interfacing port of job manager (job interface) is `50001`
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
- Refer to `test_job/parameter_server/parameter_server.py` and `test_client/client.py` to get an idea how your FL job and FL client can utilize Propius

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
<!-- - Job:
    - Edit `test_job/parameter_server/test_profile.yml` file
    -   ```bash
        $ python test_job/parameter_server/parameter_server.py test_job/parameter_server/test_profile.yml <ip> <port>
        ```
- Client:
    - Edit `test_client/test_profile.yml` file
    -   ```bash
        $ python test_client/client.py
        ``` -->
<!-- ### Propius (scheduling)
- Make changes to `global_config.yml`
- Scheduler, job manager, client manager, and load balancer launches are the same as above
- Job driver:
    ```bash
    $ python propius/job_sim/job_driver.py
    ```
- Client:
    ```bash
    $ python propius/client_sim/client_driver.py
    ``` -->



