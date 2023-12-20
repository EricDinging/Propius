# Scheduler
## Information
Job Metadata:
1. task_quota, task_budget, quota_budget
2. job_start_time, task_start_time, avg_ramp_up_time, avg_task_completion_time
3. task_alloc, task_constraints
4. task_id, job_id, type (FL|FA)

Client Metadata:
1. eligible client proportion: `get_client_proportion(constraint)`

## Boolean predicate
```python
constraint = "@CPU:[0 10], @MEM:[300 500]"
```
## Process
1. Scheduler define a mapping
2. Propius enforce constraint

## Offline
Semantics is more general
```python
@propius.jmo_offline_scheduler(jm_id=0)
def fifo(active_task_list):
    query = "@CPU:[0 inf], @MEM:[0 inf]"
    def key(job_id):
        return get_job_start_time(job_id)
    active_task_list.sort(key=key)
    # return a key value pair, key is query, value is job group
    return {query: actve_task_list}
```

## Online
Only support schedulers outputing strict one-level or two-level priority rank. Online version has less overhead.
```python
@propius.jm_online_scheduler(jm_id=0)
def fifo(active_task_list):
    def key(job_id):
        return get_job_start_time(job_id)
    active_task_list.sort(key=key)
    # return a two-dim list
    return [active_task_list]
```