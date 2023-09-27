from propius.job import Propius_job

public_constraint = {
    "cpu_f": 8,
    "ram": 6,
    "fp16_mem": 800,
    "android_os": 8
}
private_constraint = {
    "femnist_dataset_size": 150
}

job_config = {
    "public_constraint": public_constraint,
    "private_constraint": private_constraint,
    "total_round": 1000,
    "demand": 100,
    "job_manager_ip": "172.17.0.2",
    "job_manager_port": 5000,
    "ip": "172.17.0.1",
    "port": 6000,
}

propius = Propius_job(job_config)

propius.connect()
propius.register()

for round in range(job_config["total_round"]):
    propius.start_request()
    # client checking in
    propius.end_request()

    # assign client task

    # collect client response

propius.complete_job()
propius.close()

