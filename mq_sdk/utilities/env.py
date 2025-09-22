# -*- coding: utf-8 -*-
# Copyright 2019 IBM
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

import os
import json
import sys
from typing import List
import logging

from mq_sdk.utilities.types import MQAgentInfo
from mq_sdk.utilities.constants import NETWORK_TYPE

logger = logging.getLogger(__name__)


class EnvStore:
    """
      Load Envrionment Exports from local store
    """
    env = None

    MQ_ENDPOINTS = 'MQ_ENDPOINTS'
    CONNECTION_STRING = 'CONN_STRING'
    HOST = 'HOST'
    PORT = 'PORT'
    CHANNEL = 'CHANNEL'
    QUEUE_NAME = 'QUEUE_NAME'
    QMGR = 'QMGR'
    TOPIC_NAME = 'TOPIC_NAME'
    MODEL_QUEUE_NAME = 'MODEL_QUEUE_NAME'
    DYNAMIC_QUEUE_PREFIX = 'DYNAMIC_QUEUE_PREFIX'
    BACKOUT_QUEUE = 'BACKOUT_QUEUE'
    USER = 'USER'
    PASSWORD = 'PASSWORD'
    APP_USER = 'APP_USER'
    APP_PASSWORD = 'APP_PASSWORD'
    KEY_REPOSITORY = 'KEY_REPOSITORY'
    CCDT = 'MQCCDTURL'
    CIPHER = 'CIPHER'
    FILEPREFIX = "file://"
    AGENT_DESCRIPTION = 'AGENT_DESCRIPTION'
    AGENT_NAME = 'AGENT_NAME'

    def __init__(self, ccdt_path: str,network_type: NETWORK_TYPE):
        if self.env is None:

            file_path = os.path.join(ccdt_path, 'env.json')
            logger.info(
                "Looking for file %s for envrionment variables" % file_path)
            try:
                with open(file_path) as f:
                    print(f'>>>> {network_type.value}')
                    self.env = json.loads(f.read())[network_type.value]
                    print(f'>>> {self.env}')
            # Python 2
            except IOError as e:
                logger.info(
                    'I/O error reading file ({0}): {1}' % (e.errno, e.strerror))
            except ValueError:
                logger.info('Parsing error')
            except:
                logger.info('Unexpected error:')
            # Python 3
            # except FileNotFoundError:
            # logger.info("Envrionment File was not found")

    def checkEndPointIsList(self):
        if (self.env
             and self.MQ_ENDPOINTS in self.env
             and isinstance( self.env[self.MQ_ENDPOINTS], list)):
               return True
        return False

    def setEnv(self):
        if self.checkEndPointIsList():
            logger.info('Have File so ready to set envrionment variables')

            for e in self.env[self.MQ_ENDPOINTS][0]:
                os.environ[e] = self.env[self.MQ_ENDPOINTS][0][e]
                if self.PASSWORD not in e:
                    logger.info('Checking %s value is %s ' % (e, self.env[self.MQ_ENDPOINTS][0][e]))
            # Check if there are multiple endpoints defined
            if len(self.env[self.MQ_ENDPOINTS]) > 0:
               os.environ[self.CONNECTION_STRING] = self.buildConnectionString(self.env[self.MQ_ENDPOINTS])
        else:
            logger.info('No envrionment variables to set')

    def buildConnectionString(self, points):        
        l = []
        for point in points:
            if self.HOST in point and self.PORT in point:
                p = '%s(%s)' % (point[self.HOST], point[self.PORT])                
                l.append(p)
        s = ','.join(l)
        logger.info('Connection string is %s' % s)
        return s

    def getEndpointCount(self):
        if self.checkEndPointIsList():
            return len(self.env[self.MQ_ENDPOINTS])
        return 1

    def getNextConnectionString(self):
        for i, p in enumerate(self.env[self.MQ_ENDPOINTS]):
            info =  "%s(%s)" % (p[self.HOST], p[self.PORT])
            if sys.version_info[0] < 3:
                yield i, str(info)
            else:
                yield i, bytes(info, 'utf-8')

    def get_agents_info(self) -> List[MQAgentInfo]:
        agents_info: List[MQAgentInfo] = []
        for raw_endpoint in self.env[self.MQ_ENDPOINTS]:
            try:
                info = MQAgentInfo.model_validate(raw_endpoint)
                agents_info.append(info)
            except Exception as e:
                logger.error(f"Error parsing endpoint: {str(e)}")
        return agents_info


    # function to retrieve variable from Envrionment
    def getEnvValue(self, key, index = 0):
        v = os.getenv(key) if index == 0 else self.env[self.MQ_ENDPOINTS][index].get(key)
        if sys.version_info[0] < 3:
            return str(v) if v else None
        else:
            return bytes(v, 'utf-8') if v else None

    def getConnection(self, host, port):
        info = os.getenv(self.CONNECTION_STRING)
        if not info:
            info =  "%s(%s)" % (os.getenv(host), os.getenv(port))
        if sys.version_info[0] < 3:
            return str(info)
        else:
            return bytes(info, 'utf-8')

    def stringForVersion(self, data):
        if sys.version_info[0] < 3:
            return str(data)
        else:
            return bytes(data, 'utf-8')

    def ccdtCheck(self):
        fPath = self.getEnvValue(self.CCDT)
        if fPath:
            ccdtFile = fPath if not fPath.startswith(self.FILEPREFIX) else fPath[len(self.FILEPREFIX):]
            if os.path.isfile(ccdtFile):
                logger.info('CCDT file found at %s ' % ccdtFile)
                return True
        return False
    
    def getEnv(self):
        return self.env[self.MQ_ENDPOINTS]