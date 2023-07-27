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
## Usage
- Make changes to `global_config.yml`
- Scheduler:
```bash
$ python src/scheduler/scheduler.py
```
- Job manager:
```bash
$ python src/job_manager/job_manager.py
```
- Client manager:
```bash
$ python src/client_manager/client_manager.py
```
- Job driver:
```bash
$ python src/job/job_driver.py
```
- Client:
```bash
$ python src/client/client_driver.py
```

## Change to FedScale & Notes
### Client
1. `ClientConnections` will not determine aggregator address during initialization
2. Client id is assigned by propius and fedscale. These ID can be different in scheduling and training


### Job/Aggregator