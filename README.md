# Propius
Propius is a Federated Learning resource manager, capable of efficiently schedule devices in a multi-job setting, with the goal of reducing average job completion time.
## Install
- Download anaconda if not installed
    ```bash
    $ wget https://repo.anaconda.com/archive/Anaconda3-2023.03-1-Linux-x86_64.sh
    $ bash Anaconda3-2023.03-1-Linux-x86_64.sh
    $ conda list
    ```
- Navigate into `Propius` package, install and activate `propius` conda environment
    ```bash
    $ cd Propius
    $ conda env create -f environment.yml
    $ conda activate propius
    ```
- Install docker and docker-compose
    - [docker installation guide (step 1)](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-16-04)
    - [docker compose](https://docs.docker.com/compose/install/linux/#install-the-plugin-manually)
- Launch `redis-stack-search` docker image
    ```bash
    $ docker compose up -d
    ```
- Additionally, check redis server is running
    - [Install redis-cli](https://stackoverflow.com/questions/21795340/linux-install-redis-cli-only)
    - ```$ redis-cli```

## RoadMap
- [x] Enable FedScale simulation mode (pytorch, one task: femnist) with Propius
- [ ] Enable FedScale simulation mode (other framework, task) with Propius
- [ ] Scaling up & fault tolerance
- [ ] Enable FedScale simulation
- Please refer to [Project](https://github.com/users/EricDinging/projects/1) page for more info
## Usage 
### Propius + FedScale (scheduling + training/testing)
- Make changes to `global_config.yml`
- Scheduler:
    ```bash
    $ python propius/scheduler/scheduler.py
    ```
- Job manager:
    ```bash
    $ python propius/job_manager/job_manager.py
    ```
- Client manager:
    ```bash
    $ python propius/client_manager/client_manager.py
    ```
- Job:
    - Edit `propius/job/job_conf.yml` file
        ```bash
        $ python propius/job/aggregator.py propius/job/job_conf.yml
        ```
- Client:
    - Edit `propius/client/client_conf.yml` file
        ```bash
        $ python propius/client/executor.py propius/client/client_conf.yml
        ```
### Propius (scheduling)
- Make changes to `global_config.yml`
- Scheduler:
    ```bash
    $ python propius/scheduler/scheduler.py
    ```
- Job manager:
    ```bash
    $ python propius/job_manager/job_manager.py
    ```
- Client manager:
    ```bash
    $ python propius/client_manager/client_manager.py
    ```
- Job driver:
    ```bash
    $ python propius/job_sim/job_driver.py
    ```
- Client:
    ```bash
    $ python propius/client_sim/client_driver.py
    ```



