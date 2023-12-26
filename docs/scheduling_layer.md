# Scheduling Layer
## Overview
Scheduling layer sits beneath the application layer. The scheduling logic is triggered by: (1) new job registeration, (2) existing jobs' new request, (3) a certain amount of time elapse. There are two forms of scheduling logic implemented: (1) online scheduling and (2) offline scheduling.

## Online scheduling
As the client resources are highly dynamic, it is difficult to keep track of every available client resources long-term, which involves constant state checking and updates. It is therefore more appropiate to remove any state for client resources, and assign tasks to clients whenever they are available in an online fashion.

The online `scheduler` in `propius_controller` sets a score for every outstanding job based on its metadata (by interfacing with `job_db`). `client_manager` in `propius_controller` searches for an outstanding job with the highest score for every client check-in, and assign a job to an eligible client.

The online scheduling logic is invoked by either new job registration or new job request.

```python
class FIFO_scheduler(Scheduler):
    # class attributes initialization
    
    async def online(self, job_id: int):
        """Give every job which doesn't have a score yet a score of -timestamp

        Args:
            job_id: job id
        """
        
        job_timestamp = float(self.job_db_portal.get_field(job_id, "timestamp"))

        score = - (job_timestamp - self.start_time)
        self.job_db_portal.set_score(score, job_id)
```


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

