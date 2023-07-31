# -*- coding: utf-8 -*-
import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import collections
import pickle
import random
import time
import numpy as np
import torch

from argparse import Namespace
import fedscale.cloud.channels.job_api_pb2 as job_api_pb2
from fedscale.cloud.channels.channel_context import ClientConnections
#TODO tensorfloew client
from fedscale.cloud.execution.torch_client import TorchClient
from fedscale.cloud.execution.data_processor import collate #TODO voice collate fn
#TODO RL client
from fedscale.cloud.fllibs import *
from fedscale.dataloaders.divide_data import DataPartitioner, select_dataset
from propius.channels import propius_pb2
from propius.channels import propius_pb2_grpc
import yaml
from propius.util.db import geq

class Executor(object):
    """Abstract class for FedScale executor.

    Args:
        args (dictionary): Variable arguments for fedscale runtime config. 
        defaults to the setup in arg_parser.py

    """

    def __init__(self, gconfig, args):
        #TODO loggere
        self.model_adapter = None
        self.args = args
        self.num_executors = gconfig['num_executors']
        # ======== env information ========
        self.executor_id = None

        # ======== model and data ========
        self.train_dataloader = self.test_dataloader = None
        # ======== channels ========
        self.communicator = ClientConnections(
            gconfig['client_manager_ip'],
            gconfig['client_manager_port']
            )
        
        # ======== runtime information ========
        self.collate_fn = None
        #self.round = 0
        self.start_run_time = time.time()
        self.recieved_stop_request = False
        self.event_queue = collections.deque()

        #TODO wandb
        self.wandb = None
        super(Executor, self).__init__()

        # ======= propius ========
        self.id = -1
        self.gconfig = gconfig
        self.public_spec = tuple(args.public_spec)
        self.private_spec = tuple(args.private_spec)
        self.task_id = -1
        self.communicator.connect_to_cm()

    def get_client_trainer(self, conf):
        """
        Returns a framework-specific client that handles training and evaluation.
        :param conf: job config
        :return: framework-specific client instance
        """
        #TODO tensorflow
        #TODO RLclient
        return TorchClient(conf)
    
    def setup_env(self):
        """Set up experiments environment
        """
        #TODO logging
        self.setup_seed(seed=1)

    def setup_seed(self, seed=1):
        """Set random seed for reproducibility

        Args:
            seed (int): random seed

        """
        torch.manual_seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        random.seed(seed)

    def init_data(self):
        """Return the training and testing dataset

        Returns:
            Tuple of DataPartitioner class: The partioned dataset class for training and testing

        """
        #TODO train_dataset, test_dataset = init_dataset()
        if self.args.data_set == "femnist":
            from fedscale.dataloaders.femnist import FEMNIST
            from fedscale.dataloaders.utils_data import get_data_transform

            train_transform, test_transform = get_data_transform('mnist')
            train_dataset = FEMNIST(
                self.gconfig['data_dir'], dataset='train', transform=train_transform)
            test_dataset = FEMNIST(
                self.gconfig['data_dir'], dataset='test', transform=test_transform)

        #TODO various tasks
        # load data partitionxr (entire_train_data)
        #TODO logging
        training_sets = DataPartitioner(
            data=train_dataset, args=self.args, numOfClass=outputClass[args.data_set])
        #TODO training_sets.partition_data_helper(
        #     num_clients=self.args.num_participants, data_map_file=self.args.data_map_file)
        training_sets.partition_data_helper(
            num_clients=self.num_executors, data_map_file=None
        )
        testing_sets = DataPartitioner(
            data=test_dataset, args=self.args, numOfClass=outputClass[args.data_set], isTest=True)
        testing_sets.partition_data_helper(num_clients=self.num_executors)

        train_dataloader = select_dataset(self.id, training_sets, 
                                          batch_size=self.args.batch_size,
                                          args=self.args, isTest=False,
                                          collate_fn=self.collate_fn)
        test_dataloader = select_dataset(self.id, testing_sets,
                                         batch_size=self.args.test_bsz,
                                         args=self.args, isTest=True,
                                         collate_fn=self.collate_fn)
        #TODO logging

        return train_dataloader, test_dataloader

    def setup_communication(self):
        """Set up grpc connection
        """
        self.init_control_communication()
        self.init_data_communication()

    def init_control_communication(self):
        """Create communication channel between coordinator and executor.
        This channel serves control messages.
        """
        self.communicator.connect_to_server()

    def init_data_communication(self):
        """In charge of jumbo data traffics (e.g., fetch training result)
        """
        pass

    def serialize_response(self, responses):
        """Serialize the response to send to server upon assigned job completion

        Args:
            responses (string, bool, or bytes): TorchClient responses after job completion.

        Returns:
            bytes stream: The serialized response object to server.

        """
        return pickle.dumps(responses)
    
    def deserialize_response(self, responses):
        """Deserialize the response from server

        Args:
            responses (byte stream): Serialized response from server.

        Returns:
            ServerResponse defined at job_api.proto: The deserialized response object from server.

        """
        return pickle.loads(responses)
    
    def report_executor_info_handler(self):
        """Return the statistics of training dataset

        Returns:
            none

        """
        return ""
    
    def dispatch_worker_events(self, request):
        """Add new events to worker queues

        Args:
            request (string): Add grpc request from server (e.g. MODEL_TEST, MODEL_TRAIN) to event_queue.

        """
        self.event_queue.append(request)

    def client_register(self):
        """Register the executor information to the aggregator
        """
        start_time = time.time()
        while time.time() - start_time < 180:
            try:
                print(f"Client {self.executor_id}: register to parameter server")
                response = self.communicator.stub.CLIENT_REGISTER(
                    job_api_pb2.RegisterRequest(
                        client_id=self.executor_id,
                        executor_id=self.executor_id,
                        executor_info=self.serialize_response(
                            self.report_executor_info_handler()
                        )
                    )
                )
                self.dispatch_worker_events(response)
                break
            except Exception as e:
                print(e)
                #TODO logging warning
                time.sleep(5)

    def UpdateModel(self, model_weights, config):
        """Receive the broadcasted global model for current round

        Args:
            model_weights
            config (PyTorch or TensorFlow model): The broadcasted global model config

        """
        model = None
        if config['model'] == "resnet18":
            from fedscale.utils.models.specialized.resnet_speech import resnet18
            model = resnet18(num_classes=outputClass[args.data_set], in_channels=1)
        self.model_adapter = self.get_client_trainer(args).get_model_adapter(model)
        self.model_adapter.set_weights(model_weights)

    def client_ping(self):
        """Ping the aggregator for new task
        """
        print(f"Client {self.executor_id}: pinging parameter server")
        response = self.communicator.stub.CLIENT_PING(job_api_pb2.PingRequest(
            client_id=self.executor_id,
            executor_id=self.executor_id
        ))
        self.dispatch_worker_events(response)

    def Train(self, config):
        """Load train config and data to start training on that client

        Args:
            config (dictionary): The client training config.

        Returns:
            tuple (int, dictionary): The client id and train result

        """
        client_id = config['client_id']
        train_config = config['task_config']

        # if 'model' not in config or not config['model']:
        #     raise "The 'model' object must be a non-null value in the training config."
        
        client_conf = self.override_conf(train_config)
        train_res = self.training_handler(client_id=client_id,
                                          conf=client_conf)
        
        # Report execution completion meta information
        while True:
            try:
                response = self.communicator.stub.CLIENT_EXECUTE_COMPLETION(
                    job_api_pb2.CompleteRequest(
                        client_id=str(client_id),
                        executor_id=self.executor_id,
                        event=commons.CLIENT_TRAIN,
                        status=True,
                        msg=None,
                        meta_result=None,
                        data_result=None
                    )
                )
                break
            except Exception as e:
                time.sleep(0.5)

        self.dispatch_worker_events(response)

        return client_id, train_res

    def training_handler(self, client_id, conf):
        """Train model given client id

        Args:
            client_id (int): The client id.
            conf (dictionary): The client runtime config.

        Returns:
            dictionary: The train result

        """
        #self.model_adapter.set_weights(model)
        conf.client_id = client_id
        #TODO conf tokenizer
        #TODO rl training set
        client = self.get_client_trainer(self.args)
        train_res = client.train(client_data=self.train_dataloader,
                                 model=self.model_adapter.get_model(),
                                 conf = conf)
        return train_res
    
    def testing_handler(self):
        """Test model

        Args:
            args (dictionary): Variable arguments for fedscale runtime config. defaults to the setup in arg_parser.py
            config (dictionary): Variable arguments from coordinator.
        Returns:
            dictionary: The test result

        """
        test_config = self.override_conf({
            'rank': self.id,
            'memory_capacity': self.args.memory_capacity,
            'tokenizer': tokenizer
        })
        client = self.get_client_trainer(test_config)
        test_results = client.test(self.test_dataloader, self.model_adapter.get_model(), test_config)
        #TODO log result
        #TODO gc.collect()
        return test_results


    
    def Test(self, config):
        """Model Testing. By default, we test the accuracy on all data of clients in the test group

        Args:
            config (dictionary): The client testing config.

        """
        test_res = self.testing_handler()
        test_res = {'executorId': self.id, 'results': test_res}

        # Report execution completion information
        response = self.communicator.stub.CLIENT_EXECUTE_COMPLETION(
            job_api_pb2.CompleteRequest(
                client_id=self.executor_id, executor_id=self.executor_id,
                event=commons.MODEL_TEST, status=True, msg=None,
                meta_result=None, data_result=self.serialize_response(test_res)
            )
        )
        self.dispatch_worker_events(response)


    def event_monitor(self):
        """Activate event handler once receiving new message
        """
        #TODO logging
        self.client_register()

        while not self.recieved_stop_request:
            if len(self.event_queue) > 0:
                request = self.event_queue.popleft()
                current_event = request.event

                if current_event == commons.CLIENT_TRAIN:
                    print(f"Client {self.executor_id}: recieve train event")
                    train_config = self.deserialize_response(request.meta)
                    #train_model = self.deserialize_response(request.data)
                    #train_config['model'] = train_model
                    train_config['client_id'] = int(train_config['client_id'])
                    client_id, train_res = self.Train(train_config)

                    # Upload model updates
                    print(f"Client {self.executor_id}: uploading model")
                    response = self.communicator.stub.CLIENT_EXECUTE_COMPLETION(
                        job_api_pb2.CompleteRequest(
                        client_id=str(client_id),
                        executor_id=self.executor_id,
                        event=commons.UPLOAD_MODEL,
                        status=True,
                        msg=None,
                        meta_result=None,
                        data_result=self.serialize_response(train_res)
                        )
                    )
                    self.dispatch_worker_events(response)
                    # future_call.add_done_callback(
                    #     lambda _response: self.dispatch_worker_events(_response.result())
                    #     )

                elif current_event == commons.MODEL_TEST:
                    print(f"Client {self.executor_id}: recieve test event")
                    self.Test(self.deserialize_response(request.meta))

                elif current_event == commons.UPDATE_MODEL:
                    print(f"Client {self.executor_id}: recieve update model event")
                    model_weights = self.deserialize_response(request.data)
                    config = self.deserialize_response(request.meta)
                    self.UpdateModel(model_weights, config)
                
                elif current_event == commons.SHUT_DOWN:
                    print(f"Client {self.executor_id}: recieve shutdown event")
                    self.recieved_stop_request = True
                    self.Stop()
                
                elif current_event == commons.DUMMY_EVENT:
                    print(f"Client {self.executor_id}: recieve dummy event")
                    pass
            
            else:
                time.sleep(1)
                try:
                    self.client_ping()
                except Exception as e:
                    #TODO logging
                    self.Stop()

    def checkin(self)->propius_pb2.cm_offer:
        client_checkin_msg = propius_pb2.client_checkin(
            public_specification=pickle.dumps(self.public_spec)
            )
        task_offer = self.communicator.cm_stub.CLIENT_CHECKIN(
            client_checkin_msg)
        return task_offer
    
    def select_task(self, task_ids: list, private_constraints: list):
        for idx, id in enumerate(task_ids):
            if len(self.private_spec) != len(private_constraints[idx]):
                raise ValueError("Client private specification len does not match required")
            if geq(self.private_spec, private_constraints[idx]):
                self.task_id = id
                print(f"Client {self.id}: select task {id}")
                return
        self.task_id = -1
        print(f"Client {self.id}: not eligible")
        return
    
    def accept(self)->propius_pb2.cm_ack:
        client_accept_msg = propius_pb2.client_accept(client_id=self.id, task_id=self.task_id)
        cm_ack = self.communicator.cm_stub.CLIENT_ACCEPT(client_accept_msg)
        return cm_ack
    
    def run(self):
        """Start running the executor by setting up execution and communication environment, 
        and monitoring the grpc message.
        """
        cm_offer = self.checkin()
        self.id = cm_offer.client_id + 1
        self.executor_id = str(self.id)
        task_ids = pickle.loads(cm_offer.task_offer)
        task_private_constraint = pickle.loads(cm_offer.private_constraint)
        print(f"Client {self.id}: recieve client manager offer: {task_ids}")

        self.select_task(task_ids, task_private_constraint)

        if self.task_id == -1:
            print(f"Client {self.id}: Not eligible, shutting down===")
            self.communicator.cm_channel.close()
            return
        
        cm_ack = self.accept()
        if not cm_ack.ack:
            print(f"Client {self.id}: client manager not acknowledged, shutting down===")
            self.communicator.cm_channel.close()
            return
        self.communicator.aggregator_address = pickle.loads(cm_ack.job_ip)
        self.communicator.base_port = cm_ack.job_port

        # close connection to cm
        self.communicator.cm_channel.close()

        print(f"Client {self.executor_id}: setting up environment")
        self.setup_env()
        print(f"Client {self.executor_id}: initting data")
        self.train_dataloader, self.test_dataloader = self.init_data()
        print(f"Client {self.executor_id}: setting up communication")
        self.setup_communication()
        print(f"Client {self.executor_id}: registering to job")
        self.event_monitor()

    def Stop(self):
        """Stop the current executor
        """
        #logging.info(f"Terminating the executor ...")
        #TODO logging
        self.communicator.close_server_connection()
        self.received_stop_request = True
        # if self.wandb != None:
        #     self.wandb.finish()
        #TODO wandb

    def override_conf(self, config):
        """ Override the variable arguments for different client

        Args:
            config (dictionary): The client runtime config.

        Returns:
            dictionary: Variable arguments for client runtime config.

        """
        default_conf = vars(self.args).copy()

        for key in config:
            default_conf[key] = config[key]

        return Namespace(**default_conf)
    

if __name__ == "__main__":
    global_setup_file = './global_config.yml'

    if len(sys.argv) != 2:
        print("Wrong format: python propius/client/executor.py <config file>")
        exit(1)

    with open(global_setup_file, 'r') as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            config_file = str(sys.argv[1])
            with open(config_file, 'r') as config_file:
                args = yaml.load(config_file, Loader=yaml.FullLoader)
                print("Client reads config successfully")

                args = Namespace(**args)
                executor = Executor(gconfig, args)
                executor.run()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)
        
