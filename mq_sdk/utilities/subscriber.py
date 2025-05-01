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

import pymqi
import logging

from .env import EnvStore  
from mq_sdk.utilities.constants import NETWORK_TYPE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MQSubscriber:    
    def __init__(self, ccdt_path: str):        
        self.envStore = EnvStore(
            ccdt_path = ccdt_path,
            network_type = NETWORK_TYPE.STATE_NETWORK 
        )
        self.envStore.setEnv()
        
        self.MQDetails = {}
        self.credentials = {
            self.envStore.USER: self.envStore.getEnvValue(self.envStore.APP_USER),
            self.envStore.PASSWORD: self.envStore.getEnvValue(self.envStore.APP_PASSWORD)
        }
        self.buildMQDetails()
        self.conn_info = self.envStore.getConnection(self.envStore.HOST, self.envStore.PORT)

        self.qmgr = None
        self.subscription = None

    def buildMQDetails(self):        
        for key in [self.envStore.QMGR, self.envStore.TOPIC_NAME, self.envStore.CHANNEL,
                    self.envStore.HOST, self.envStore.PORT, self.envStore.KEY_REPOSITORY, self.envStore.CIPHER]:
            self.MQDetails[key] = self.envStore.getEnvValue(key)

    def connect(self):        
        logger.info('Establishing connection with MQ Server')
        try:
            cd = None
            if True:
                logger.info('CCDT URL export is not set; using JSON environment client connection settings.')
                cd = pymqi.CD(Version=pymqi.CMQXC.MQCD_VERSION_11)
                cd.ChannelName = self.MQDetails[self.envStore.CHANNEL]
                cd.ConnectionName = self.conn_info
                cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
                cd.TransportType = pymqi.CMQC.MQXPT_TCP

                logger.info('Checking cipher details')
                if self.MQDetails[self.envStore.CIPHER]:
                    logger.info('Using cipher details')
                    cd.SSLCipherSpec = self.MQDetails[self.envStore.CIPHER]
                    
            sco = pymqi.SCO()
            if self.MQDetails[self.envStore.KEY_REPOSITORY]:
                logger.info('Setting key repository')
                sco.KeyRepository = self.MQDetails[self.envStore.KEY_REPOSITORY]

            options = pymqi.CMQC.MQPMO_NEW_CORREL_ID

            self.qmgr = pymqi.QueueManager(None)
            self.qmgr.connect_with_options(self.MQDetails[self.envStore.QMGR],
                                           user=self.credentials[self.envStore.USER],
                                           password=self.credentials[self.envStore.PASSWORD],
                                           opts=options, cd=cd, sco=sco)
            logger.info('Connection established')
            return self.qmgr

        except pymqi.MQMIError as e:
            logger.error("Error connecting to MQ Server")
            logger.error(e)
            return None

    def getSubscription(self):        
        logger.info('Connecting to subscription')
        try:
            sub_desc = pymqi.SD()
            sub_desc["Options"] = (
                pymqi.CMQC.MQSO_CREATE +
                pymqi.CMQC.MQSO_RESUME +
                pymqi.CMQC.MQSO_DURABLE +
                pymqi.CMQC.MQSO_MANAGED
            )
            sub_desc.set_vs("SubName", "MySub")
            print(f'>>>> Using the following details: {self.MQDetails}')
            sub_desc.set_vs("ObjectString", self.MQDetails[self.envStore.TOPIC_NAME])

            if self.qmgr is None:
                logger.error("Queue manager is not connected")
                return None

            self.subscription = pymqi.Subscription(self.qmgr)
            self.subscription.sub(sub_desc=sub_desc)
            logger.info("Subscription established")
            return self.subscription

        except pymqi.MQMIError as e:
            logger.error("Error creating subscription")
            logger.error(e)
            return None
    
    def getMessageConfig(self):
        subOptions = (
            pymqi.CMQC.MQGMO_NO_SYNCPOINT +
            pymqi.CMQC.MQGMO_FAIL_IF_QUIESCING +
            pymqi.CMQC.MQGMO_WAIT +
            pymqi.CMQC.MQGMO_NO_PROPERTIES
        )

        gmo = pymqi.GMO(Options=subOptions)
        gmo["WaitInterval"] = 30 * 1000
        md = pymqi.MD()        

        return md, gmo
        
    def resetMD(self, md):
        md.MsgId = pymqi.CMQC.MQMI_NONE
        md.CorrelId = pymqi.CMQC.MQCI_NONE
        md.GroupId = pymqi.CMQC.MQGI_NONE 
        return md

    def subscribe(self):
        logger.info("MQSubscriber: Starting subscription process")
        self.connect()
        if self.qmgr:
            self.getSubscription()
        if self.subscription:
            return True
        else:
            return False

    def close():
        self.subscription.close(sub_close_options=pymqi.CMQC.MQCO_KEEP_SUB, close_sub_queue=True)
        self.qmgr.disconnect()




