# Binding layer

## Process
1. Client check-in, reporting its public attributes
2. `client_manager` insert the client into `client_db`
If `propius_controller` uses online scheduling
3. `client_manager` returns eligible tasks as well as their private constraints to the client in a task offer list. All the selected tasks should have a `demand` greater than `amount`, and constraint satisfied by the client attributes. The returned tasks are sorted according to the scheduling algorithm.

4. If a client does not receive available tasks, it will continuously ping `client_manager` until a task is assigned and binded with the client, or the client becomes unavailable.
5. The client performs local task selection based on its private attributes (eg. dataset size) and task constraints. When decisions are made, the client reports back the task selected. `client_manager` then increments the selected task allocation number in `job_db` if the selected task is still available, and returns the task network addresses to the client. If the job allocation amount is equal to its demand for this round, the job is removed from outstanding job list, and subsequent checked-in clients will not receive task binding from this job until the job makes another request.

## Client Database
Recent client metadata is stored in a database. The information, such as client attribute distribution, can be highly useful for schedulers.
### Schema
This is the metadata for recent client. We use Redis JSON key-value store, where key is the `client_id`. Each client entry has an expiration time.
|Field Name|Data Type|Description| 
|--|--|--|
|timestamp | numeric | job register time|
|public_attribute.[x]| numeric | client attribute value for constraint x |

## Temporary Client Store
If offline scheduling is used for better flexibility, we use a small client datastore to memorize state of most recently available clients, and task allocation information for every client in the datastore. The datastore is co-located with `client_database` in the same Redis server.
### Schema
This is the metadata for recent client. We use Redis JSON key-value store, where key is the `client_id`. Each client entry has a short expiration time of 25 seconds.
|Field Name|Data Type|Description| 
|--|--|--|
|job_ids | Text | available jobs |
|option| Numeric | an optional field for storing client metadata (eg. speed of last round) |
|public_attribute.[x]| numeric | client attribute value for constraint x |


