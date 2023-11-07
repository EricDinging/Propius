# Allocation
## Component
- Router
- Job manager (Datastore, [scheduler, portal])
- Client manager
- Reducer
## Problem
Each request has demand, constraints (private, public, geographic), task_id, job_id. 
Public constraints are taken care of by the scheduler. Private constraints are taken care of by client local selection.
Geographic constraints are taken care of by the router.

The question is how to manage demand and allocation in distributed resource management system

## Assumptions
- Only one active task for one job in the system. New task will override existing task

## Ideas
1. Split demand across various pillars and client managers. Problem, straggler issue, leading to higher ramp-up latency
2. Expose the demand to every eligible client manager. Reducer will report back the global allocation, and then the remaining demand will be redistributed for allocation. Two planes: resource allocation planes (per 3 seconds), resource plane

## Potential Issues and solutions
1. Synchronization of states across job manager -> Central reducer and router control state update
2. Old report overwrite new task request -> check task_id when updating state, keep the latest task_id
3. Double count allocation -> Clear client manager allocation once scanned by reducer

## State Update Activation
1. New request
2. Reducer report

## Redistribution Activation
1. Reducer report

## Router
```python
def new_checkin(constraints, demand):
    job_id = assign_job_id()
    return job_id
    
def new_request(job_id, constraints, demand):
    jm_list = find_jm(constraints.geo)
    task_id = assign_task_id(job_id)
    for jm in jm_list:
        jm.new_request(job_id, task_id, constraints, demand)
```

## Job manager
```python
# job_table job_id -> (task_id, constraints, demand, alloc)
def new_request(job_id, task_id, constraints, demand):
    # overwrite or append
    job_table[job_id] = {
        "task_id": task_id, 
        "constraints": constraints, 
        "demand": demand,
        "alloc": 0 
    }

# report_bale job_id -> (task_id, cur_alloc)
# RPC service function for reducer
# cm_list
def new_report(report_table):
    for job_id, metadata in report_table.items():
        task_id = metadata["task_id"]
        cur_alloc = metadata["cur_alloc"]
        if job_id in job_table:
            # neglect stale report
            if task_id == job_table[job_id]["task_id"]:
                job_table[job_id]["alloc"] =  min(cur_alloc + job_table[job_id]["alloc"], job_table[job_id]["demand"])

    # update_table job_id -> (task_id, constraints, rem_demand, local_cur_alloc), sorted or grouped by scheduler
    # calcuate remaining demand for each job in this step, do not include jobs with alloc=demand
    # local_cur_alloc = 0
    # Do not need to include all the active tasks, only the tasks with highest priorities
    update_table = scheduler(job_table)
    for cm in cm_list:
        cm.update_cm_table(update_table)
```

## Client Manager
```python
# cm_job_table job_id -> (task_id, constraints, rem_demand, local_cur_alloc), sorted or grouped
def reducer_scan():
    reduce_table = []
    for job_id, metadata in cm_job_table.items():
        reduce_table[job_id] = {
            "task_id": metadata["task_id"]
            "local_cur_alloc": metadata["local_cur_alloc"]
        }
        metadata["local_cur_alloc"] = 0
    return reduce_table

def update_cm_table(update_table):  
    for job_id, metadata in update_table:
        if job_id in cm_job_table:
            metadata["local_cur_alloc"] += cm_job_table["job_id"]["local_cur_alloc"]
    cm_job_table = update_table

def client_check_in(attributes):
    # Find suitable task based on priority, and constraints
    (job_id, task_id) = select_task(attributes)

    cm_job_table["job_id"]["local_cur_alloc"] += 1
```

## Reducer
```python
# execute periodically
# cm_list
# jm_list
def reduce_routine():
    # reduce_table job_id -> (task_id, cur_alloc)
    reduce_table = []
    for cm in cm_list:
        reduce(cm, reduce_table)
    for jm in jm_list:
        report(jm, reduce_table)

def reduce(cm, reduce_table):
    cm_reduce_table = cm.reducer_scan()
    for job_id, metadata in cm_reduce_table:
        if job_id in reduce_table:
            if metadata["task_id"] < reduce_table["job_id"]["task_id"]:
                continue
            elif metadata["task_id"] == reduce_table["job_id"]["task_id"]:
                reduce_table["job_id"]["cur_alloc"] += metadata["local_cur_alloc"]
            else:
                # overwrite
                reduce_table["job_id"] = metadata
        else:
            # append
            reduce_table["job_id"] = metadata

def report(jm, reduce_table):
    jm.new_report(reduce_table)
```
