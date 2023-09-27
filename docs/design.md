# Design


## Job metadata
Propius will make estimations about total round $r_{total}$, total demand $d_{total}$, remaining demand $d_r$, and remaining time $t_r$ based on the information provided when job checks in.

Propius keeps track of current demand (of current round) $d$, attained demand (service) $d_a$, current round number $r$, job runtime $t$, job check in time $t_0$.

Jobs may specify different $d$ for different $r$.
1. Job provides total round estimation $r_{total}$
    - $d_{total} = d_a + (r_{total} - r) \times d$
    - $d_r = d_{total} - d_a$
    - $t_r = t / r \times (r_{total} - r)$
2. Job does not provide total round estimation
    - $r_{total} = 2 \times r$
    - $d_{total} = 2 \times d_a$
    - $d_r = d_{total} - d_a$
    - $t_r = 2 \times t$

## Scheduling algorithm
Propius will calculate a priority score $s$ for every job. A job has higher priority if its score is higher.
1. FIFO
    - Calculate the score upon job check in (only once)
    - $s = -t_0$
2. RANDOM
    - Random sampling at the client end
3. SRTF
    - Calculate the score upon job request (every round)
    - $s = -t_r$
4. SRDF
    - Calculate the score upon job request (every round)
    - $s = -d_r$
5. IRS (AMG)
    - Calculate the score upon job check in (only once)
6. LAS
    - Calculate the score upon job request (every round)
    - $s = -d_a$

## Job lifetime
- Job will be removed if runtime is greater than JOB_EXPIRE_TIME
- Job will be removed if time intervals is greater than JOB_MAX_SILENT_TIME
- If use policy that removes job after reaching the estimated round
    - If job provides total round estimation $r_{total}$
        - Job will be removed after $r_{total}$ 
    - Job does not provide total round estimation
        - Job will be removed after MAX_ROUND