from propius_controller.client import Propius_client
 
# make some system calls to get device specs

public_specifications = {
    "cpu_f": 8,
    "ram": 6,
    "fp16_mem": 800,
    "android_os": 8
}

private_specifications = {
    "femnist_dataset_size": 150
}

client_config = {
    "public_specifications": public_specifications,
    "load_balancer_ip": "172.17.0.3",
    "load_balancer_port": 50001
}

propius = Propius_client(client_config)


def select_task(task_ids, task_private_constraints):
    # select task according to local private constraints
    pass


while True:
    # make system calls to get device condition
    condition = True
    if condition:
        propius.connect()

        propius.client_check_in()

        task_ids, task_private_constraints = propius.client_ping(num_trial=5)

        task_id = select_task(task_ids, task_private_constraints)

        job_ip, job_port = propius.client_accept(task_id)

        propius.close()

        # check-in to job
        # receive task
        # perform task
        # report to job 