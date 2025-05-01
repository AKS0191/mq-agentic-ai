# -*- coding: utf-8 -*-
# © Copyright IBM Corporation 2024, 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from mq_sdk.utilities.env import EnvStore
import json
import datetime
import pymqi
import random

import logging
from mq_sdk.utilities.constants import NETWORK_TYPE

class MQRequest:

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    def __init__(self, ccdt_path: str):        
        self.envStore = EnvStore(
            ccdt_path=ccdt_path,
            network_type=NETWORK_TYPE.OUTBOUND_NETWORK
        )
        self.envStore.setEnv()
        self.MQDetails = {}

        self.credentials = {
            self.envStore.USER : self.envStore.getEnvValue(self.envStore.APP_USER),
            self.envStore.PASSWORD : self.envStore.getEnvValue(self.envStore.APP_PASSWORD)
        }
        self.buildMQDetails()

        self.logger.info('Credentials are set')

        self.conn_info = self.envStore.getConnection(self.envStore.HOST, self.envStore.PORT)

        self.msgObject = {
            'Greeting': "Hello from Python! " + str(datetime.datetime.now()),
            'value': random.randint(1, 101)
        }

        self.logger.info('Connection is %s' % self.conn_info)

        self.qmgr = None
        self.queue = None

        self.dynamic = {
            'queue' : None, 
            'name'  : None
        }

        self.msgid = None
        self.correlid = None
        

    def perform_connection(self):
        self.qmgr = self.connect()
    
    def put_and_wait_response(self, message):
        if (self.qmgr):
            self.queue = self.get_queue()
        
        if (self.queue):
            self.dynamic['queue'], self.dynamic['name'] = self.get_dynamic_queue()    

        if (self.dynamic['queue']):
            self.logger.info('Checking dynamic Queue Name')
            self.logger.info(self.dynamic['name'])
            msgid, correlid = self.putMessage(message)
            if msgid:
                response = self.awaitResponse(msgid, correlid)
                return response
                
            self.dynamic['queue'].close()
            
        
        if(self.queue):
            self.queue.close()
        
        if(self.qmgr):
            self.qmgr.disconnect()
        
        self.logger.info("Application is closing...")

    
    def buildMQDetails(self):
        for key in [self.envStore.QMGR, self.envStore.QUEUE_NAME, self.envStore.CHANNEL, self.envStore.HOST,
                self.envStore.PORT, self.envStore.MODEL_QUEUE_NAME, self.envStore.DYNAMIC_QUEUE_PREFIX,
                self.envStore.KEY_REPOSITORY, self.envStore.CIPHER]:
            self.MQDetails[key] = self.envStore.getEnvValue(key)

    def get_dynamic_queue(self):
        self.logger.info('Connecting to Dynmic Queue')
        try:
            # Dynamic queue's object descriptor.
            dyn_od = pymqi.OD()
            self.logger.info(self.MQDetails[self.envStore.MODEL_QUEUE_NAME])
            self.logger.info(self.MQDetails[self.envStore.DYNAMIC_QUEUE_PREFIX])
            dyn_od.ObjectName = self.MQDetails[self.envStore.MODEL_QUEUE_NAME]
            dyn_od.DynamicQName = self.MQDetails[self.envStore.DYNAMIC_QUEUE_PREFIX]

            # Open the dynamic queue.
            dyn_input_open_options = pymqi.CMQC.MQOO_INPUT_EXCLUSIVE
            dyn_queue = pymqi.Queue(self.qmgr, dyn_od, dyn_input_open_options)
            self.logger.info("CREATED DYN QUEUE: " + str(dyn_queue))
            dynamicQueueName = dyn_od.ObjectName.strip()
            self.logger.info('Dynamic Queue Details are')
            self.logger.info(dynamicQueueName)

            return dyn_queue, dynamicQueueName

        except pymqi.MQMIError as e:
            self.logger.error("Error getting queue")
            self.logger.error(e)
            return None

    
    def get_queue(self):
        self.logger.info('Connecting to Queue')
        try:
            # Can do this in one line, but with an Object Descriptor
            # can or in more options.
            # q = pymqi.Queue(qmgr, MQDetails[self.envStore.QUEUE_NAME])
            q = pymqi.Queue(self.qmgr)

            od = pymqi.OD()
            od.ObjectName = self.MQDetails[self.envStore.QUEUE_NAME]
            q.open(od, pymqi.CMQC.MQOO_OUTPUT)
            self.logger.info('Connected to queue ' + str(self.MQDetails[self.envStore.QUEUE_NAME]))
            return q
        except pymqi.MQMIError as e:
            self.logger.error("Error getting queue")
            self.logger.error(e)
            return None


    def connect(self):
        self.logger.info('Establising Connection with MQ Server')
        try:
            cd = None
            if not self.envStore.ccdtCheck():
                self.logger.info('CCDT URL export is not set, will be using json envrionment client connections settings')

                cd = pymqi.CD(Version=pymqi.CMQXC.MQCD_VERSION_11)
                cd.ChannelName = self.MQDetails[self.envStore.CHANNEL]
                cd.ConnectionName = self.conn_info
                cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
                cd.TransportType = pymqi.CMQC.MQXPT_TCP

                self.logger.info('Checking Cypher details')
                # If a cipher is set then set the TLS settings
                if self.MQDetails[self.envStore.CIPHER]:
                    self.logger.info('Making use of Cypher details')
                    cd.SSLCipherSpec = self.MQDetails[self.envStore.CIPHER]

            # Key repository is not specified in CCDT so look in envrionment settings
            # Create an empty SCO object
            sco = pymqi.SCO()
            if self.MQDetails[self.envStore.KEY_REPOSITORY]:
                self.logger.info('Setting Key repository')
                sco.KeyRepository = self.MQDetails[self.envStore.KEY_REPOSITORY]

            #options = pymqi.CMQC.MQPMO_NO_SYNCPOINT | pymqi.CMQC.MQPMO_NEW_MSG_ID | pymqi.CMQC.MQPMO_NEW_CORREL_ID
            options = pymqi.CMQC.MQPMO_NEW_CORREL_ID

            qmgr = pymqi.QueueManager(None)
            
            qmgr.connect_with_options(self.MQDetails[self.envStore.QMGR],
                                    user=self.credentials[self.envStore.USER],
                                    password=self.credentials[self.envStore.PASSWORD],
                                    opts=options, cd=cd, sco=sco)
            return qmgr

        except pymqi.MQMIError as e:
            self.logger.error("Error connecting")
            self.logger.error(e)
            return None

    def putMessage(self, msgObject):
        self.logger.info('Attempting put to Queue')
        try:
            # queue.put(json.dumps(msgObject).encode())
            # queue.put(json.dumps(msgObject))

            # Prepare a Message Descriptor for the request message.
            self.logger.info('Dynamic Queue Name is ')
            self.logger.info(self.dynamic['name'])
            md = pymqi.MD()
            md.ReplyToQ = self.dynamic['name']
            md.MsgType = pymqi.CMQC.MQMT_REQUEST
            md.Format = pymqi.CMQC.MQFMT_STRING

            # Send the message and ReplyToQ destination        
            self.queue.put(self.envStore.stringForVersion((json.dumps(msgObject))), md)
            
            self.logger.info("Put message successful")
            #logger.info(md.CorrelID)
            return md.MsgId, md.CorrelId
            # return md.CorrelId
        except pymqi.MQMIError as e:
            self.logger.error("Error in put to queue")
            self.logger.error(e)

    def awaitResponse(self, msgId, correlId):
        self.logger.info('Attempting get from Reply Queue')

        # Message Descriptor
        md = pymqi.MD()
        md.MsgId = msgId
        md.CorrelId = correlId

        # Get Message Options
        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_WAIT | \
                        pymqi.CMQC.MQGMO_FAIL_IF_QUIESCING | \
                        pymqi.CMQC.MQGMO_NO_PROPERTIES
        gmo.WaitInterval = 5000  # 5 seconds
        #gmo.MatchOptions = pymqi.CMQC.MQMO_MATCH_MSG_ID
        gmo.MatchOptions = pymqi.CMQC.MQMO_MATCH_CORREL_ID
        gmo.Version = pymqi.CMQC.MQGMO_VERSION_2

        keep_running = True
        while keep_running:
            try:
                # Wait up to to gmo.WaitInterval for a new message.
                message = self.dynamic['queue'].get(None, md, gmo)

                # Process the message here..
                msgObject = json.loads(message.decode())
                self.logger.info('Have reply message from Queue')
                self.logger.info(msgObject)
                return msgObject

                # Not expecting any more messages
                keep_running = False

            except pymqi.MQMIError as e:
                if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE:
                    # No messages, that's OK, we can ignore it.
                    pass
                else:
                    # Some other error condition.
                    raise

            except (UnicodeDecodeError, ValueError) as e:
                self.logger.info('Message is not valid json')
                self.logger.info(e)
                self.logger.info(message)
                continue

            except KeyboardInterrupt:
                self.logger.info('Have received a keyboard interrupt')
                keep_running = False
