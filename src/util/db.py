import redis
from redis.commands.json.path import Path
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
import time
import json

class Job_db:
    def __init__(self, gconfig):
        host = gconfig['db_ip']
        port = int(gconfig['db_port'])
        self.r = redis.Redis(host=host, port=port)
        self.sched_alg = gconfig['sched_alg']

        schema = (
          NumericField("$.job.timestamp", as_name="timestamp"), #job register time
          NumericField("$.job.total_sched", as_name="total_sched"), #total amount of sched time
          NumericField("$.job.start_sched", as_name="start_sched"), #last round start time
          NumericField("$.job.constraints.cpu", as_name="cpu"),
          NumericField("$.job.constraints.memory", as_name="memory"),
          NumericField("$.job.constraints.os", as_name="os"),
          TextField("$.job.ip", as_name="ip"),
          NumericField("$.job.port", as_name="port"),
          NumericField("$.job.total_demand", as_name="total_demand"),
          NumericField("$.job.total_round", as_name="total_round"),
          NumericField("$.job.round", as_name="round"),
          NumericField("$.job.demand", as_name="demand"),
          NumericField("$.job.amount", as_name="amount"),
          NumericField("$.job.score", as_name="score"),
          )
        
        try:
            self.r.ft("job").create_index(schema, 
                    definition=IndexDefinition(prefix=["job:"], index_type=IndexType.JSON))
        except:
            pass
    
    def flushdb(self):
        self.r.flushdb()

    def get_job_size(self)->int:
        info = self.r.ft('job').info()
        return int(info['num_docs'])

class Client_db:
    def __init__(self, gconfig):
        host = gconfig['db_ip']
        port = int(gconfig['db_port'])
        self.r = redis.Redis(host=host, port=port)
        #self.max_size = int(gconfig['client_db_maxsize'])
        self.start_time = int(time.time())
        self.client_ttl = int(gconfig['client_expire_time'])

        schema = (
          NumericField("$.client.timestamp", as_name="timestamp"),
          NumericField("$.client.cpu", as_name="cpu"),
          NumericField("$.client.memory", as_name="memory"),
          NumericField("$.client.os", as_name="os"))
        
        try:
            self.r.ft("client").create_index(schema, 
                    definition=IndexDefinition(prefix=["client:"], index_type=IndexType.JSON))
        except:
            pass

    def flushdb(self):
        self.r.flushdb()

def geq(t1:tuple[int, int, int], t2:tuple[int, int, int])->bool:
    for idx in range(len(t1)):
        if t1[idx] < t2[idx]:
            return False
    return True