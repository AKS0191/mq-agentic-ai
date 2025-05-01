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
import datetime
import pymqi

import logging

from mq_sdk.utilities.env import EnvStore
from mq_sdk.utilities.constants import NETWORK_TYPE
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlightEmitter:    
    MQDetails = {}
    credentials = {}

    def __init__(self, envstore_path):
        self.envStore = EnvStore(
            envstore_path,
            network_type=NETWORK_TYPE.STATE_NETWORK
        )
        self.envStore.setEnv()
        
        self.credentials = {
            self.envStore.USER: self.envStore.getEnvValue(self.envStore.APP_USER),
            self.envStore.PASSWORD: self.envStore.getEnvValue(self.envStore.APP_PASSWORD)
        }


    def connect(self):
        logger.info('Establising Connection with MQ Server')
        try:
            cd = None
            if not self.envStore.ccdtCheck():
                logger.info('CCDT URL export is not set, will be using json envrionment client connections settings')

                cd = pymqi.CD(Version=pymqi.CMQXC.MQCD_VERSION_11)
                cd.ChannelName = self.MQDetails[self.envStore.CHANNEL]
                cd.ConnectionName = self.envStore.getConnection(self.envStore.HOST, self.envStore.PORT)
                cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
                cd.TransportType = pymqi.CMQC.MQXPT_TCP

                logger.info('Checking Cypher details')
                if self.MQDetails[self.envStore.CIPHER]:
                    logger.info('Making use of Cypher details')
                    cd.SSLCipherSpec = self.MQDetails[self.envStore.CIPHER]
            
            sco = pymqi.SCO()
            if self.MQDetails[self.envStore.KEY_REPOSITORY]:
                logger.info('Setting Key repository')
                sco.KeyRepository = self.MQDetails[self.envStore.KEY_REPOSITORY]
            
            options = pymqi.CMQC.MQPMO_NEW_CORREL_ID

            qmgr = pymqi.QueueManager(None)
            qmgr.connect_with_options(self.MQDetails[self.envStore.QMGR],
                                    user=self.credentials[self.envStore.USER],
                                    password=self.credentials[self.envStore.PASSWORD],
                                    opts=options, cd=cd, sco=sco)
            return qmgr
        except pymqi.MQMIError as e:
            logger.error("Error connecting")
            logger.error(e)
            return None

    
    def getTopic(self,qmgr):
        logger.info('Connecting to Topic')
        try:
            t = pymqi.Topic(qmgr, topic_string=self.MQDetails[self.envStore.TOPIC_NAME])
            t.open(open_opts=pymqi.CMQC.MQOO_OUTPUT)
            return t
        except pymqi.MQMIError as e:
            logger.error("Error getting topic")
            logger.error(e)
            return None


    def publishMessage(self, object=None):
        self.buildMQDetails()

        logger.info('Credentials are set')                        

        msgObjectJson = {
                'Message': "New Price Available " + str(datetime.datetime.now()),
                'Object': object
        }

        qmgr = None
        topic = None

        qmgr = self.connect()
        if (qmgr):
            topic = self.getTopic(qmgr)            
            if (topic):
                logger.info("Application is closing")
            logger.info('Attempting publish to Topic')
            try:
                md = pymqi.MD()
                md.Format = pymqi.CMQC.MQFMT_STRING                
                topic.pub(self.envStore.stringForVersion(json.dumps(msgObjectJson)), md)
                logger.info("Publish message successful")
            except pymqi.MQMIError as e:
                logger.error("Error in publish to topic")
                logger.error(e)
            
            topic.close()

        if (qmgr):
            qmgr.disconnect()

        
    def buildMQDetails(self):
        for key in [self.envStore.QMGR, self.envStore.CHANNEL, self.envStore.HOST,
                    self.envStore.PORT, self.envStore.KEY_REPOSITORY, self.envStore.CIPHER, self.envStore.TOPIC_NAME]:
            self.MQDetails[key] = self.envStore.getEnvValue(key)
