# Propius
Propius is a Federated Learning resource manager, capable of efficiently schedule devices in a multi-job setting, with the goal of reducing average job completion time.
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
```bash
cd Propius
conda env create -f environment.yml
conda activate propius
conda install pytorch==1.12.1 torchvision==0.13.1 torchaudio==0.12.1 cudatoolkit=11.3 -c pytorch
```
- Install docker and docker-compose
    - [docker installation guide (step 1)](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-16-04)
    - [docker compose](https://docs.docker.com/compose/install/linux/#install-the-plugin-manually)
- Launch `redis-stack-search` docker image (for system distribution, lanuch a database instance on a specific node)
```bash
docker compose -f docker/job_db.yml up -d
docker compose -f docker/client_db_0.yml up -d
```
- If there is an error saying that you cannot connect to docker daemon, try [this](https://stackoverflow.com/questions/48957195/how-to-fix-docker-got-permission-denied-issue)
    
- Additionally, check redis server is running
    - [Install redis-cli](https://stackoverflow.com/questions/21795340/linux-install-redis-cli-only)
```bash
$ redis-cli -h localhost -p 6379 ping
$ redis-cli -h localhost -p 6380 ping
```

## RoadMap
- Please refer to [Project](https://github.com/users/EricDinging/projects/1) page for more info
## Usage
### Propius
- Download dataset using FedScale (will be included in this library later)
- Make changes to `propius/global_config.yml`
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
    $ python propius/client_manager/client_manager.py 0
    $ python propius/client_manager/client_manager.py 1
    ...
    ```
- Load balancer:
    ```bash
    $ python propius/load_balancer/load_balancer.py
    ```
### Interface
- Propius' job interface is defined in `propius_job/propius_job.py`
- Propius' client interface is defined in `propius_client/propius_client.py`
- Refer to `test_job/parameter_server/parameter_server.py` and `test_client/client.py` to get an idea how your FL job and FL client can utilize Propius

### Propius Simulator
- Under construction
### Evaluation
- Try out new scheduling algorithm
- Large evaluation framework is under construction

### Testing
- Under construction
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



