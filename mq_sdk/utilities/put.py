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
import pymqi
import logging
from .env import EnvStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MQPut:
    def __init__(self):
        self.logger = logger
        # Initialize EnvStore
        self.envStore = EnvStore("../../")
        self.envStore.setEnv()

        # Build MQDetails and credentials dictionaries
        self.MQDetails = {}
        self.credentials = {
            self.envStore.USER: self.envStore.getEnvValue(self.envStore.APP_USER),
            self.envStore.PASSWORD: self.envStore.getEnvValue(self.envStore.APP_PASSWORD)
        }
        self._build_mq_details()

        # Build connection information
        self.conn_info = self.envStore.getConnection(self.envStore.HOST, self.envStore.PORT)
        self.logger.info("Connection is %s", self.conn_info)

        # Initialize connection and queue attributes
        self.qmgr = None
        self.queue = None

        # Connect to Queue Manager and open the queue
        self._connect()
        if self.qmgr:
            self._get_queue()

    def _build_mq_details(self):
        """Populate MQDetails using environment values."""
        keys = [
            self.envStore.QMGR,
            self.envStore.QUEUE_NAME,
            self.envStore.CHANNEL,
            self.envStore.HOST,
            self.envStore.PORT,
            self.envStore.KEY_REPOSITORY,
            self.envStore.CIPHER
        ]
        for key in keys:
            self.MQDetails[key] = self.envStore.getEnvValue(key)
        self.logger.info("MQ Details: %s", self.MQDetails)

    def _connect(self):
        """Establish connection to the MQ Queue Manager."""
        self.logger.info("Establishing connection with MQ Server")
        try:
            cd = None
            if not self.envStore.ccdtCheck():
                self.logger.info("CCDT URL export is not set, using JSON environment client connection settings")
                cd = pymqi.CD(Version=pymqi.CMQXC.MQCD_VERSION_11)
                cd.ChannelName = self.MQDetails[self.envStore.CHANNEL]
                cd.ConnectionName = self.conn_info
                cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
                cd.TransportType = pymqi.CMQC.MQXPT_TCP

                # If a cipher is set, then set the TLS settings
                if self.MQDetails[self.envStore.CIPHER]:
                    self.logger.info("Making use of cipher details")
                    cd.SSLCipherSpec = self.MQDetails[self.envStore.CIPHER]

            # Create an empty SCO (SSL Configuration Object)
            sco = pymqi.SCO()
            if self.MQDetails[self.envStore.KEY_REPOSITORY]:
                self.logger.info("Setting Key Repository")
                sco.KeyRepository = self.MQDetails[self.envStore.KEY_REPOSITORY]

            # Set connection options; you can adjust these if needed
            options = pymqi.CMQC.MQPMO_NEW_CORREL_ID

            self.qmgr = pymqi.QueueManager(None)
            self.qmgr.connect_with_options(
                self.MQDetails[self.envStore.QMGR],
                user=self.credentials[self.envStore.USER],
                password=self.credentials[self.envStore.PASSWORD],
                opts=options, cd=cd, sco=sco
            )
            self.logger.info("Connected to Queue Manager: %s", self.MQDetails[self.envStore.QMGR])
        except pymqi.MQMIError as e:
            self.logger.error("Error connecting to MQ Server")
            self.logger.error(e)

    def _get_queue(self):
        """Open the MQ queue for output."""
        self.logger.info("Connecting to Queue")
        try:
            q = pymqi.Queue(self.qmgr)
            od = pymqi.OD()
            od.ObjectName = self.MQDetails[self.envStore.QUEUE_NAME]
            q.open(od, pymqi.CMQC.MQOO_OUTPUT)
            self.queue = q
            self.logger.info("Connected to Queue: %s", self.MQDetails[self.envStore.QUEUE_NAME])
        except pymqi.MQMIError as e:
            self.logger.error("Error getting queue")
            self.logger.error(e)

    def put(self, message: dict):
        """Put a message onto the queue. The message is assumed to be a dict and will be JSON-dumped."""
        self.logger.info("Attempting to put message to Queue")
        try:
            md = pymqi.MD()
            md.Format = pymqi.CMQC.MQFMT_STRING

            # Create a string from the message object and modify it for versioning if necessary.
            msg_str = json.dumps(message)
            final_msg = self.envStore.stringForVersion(msg_str)
            self.queue.put(final_msg, md)
            self.logger.info("Put message successful")
        except pymqi.MQMIError as e:
            self.logger.error("Error in putting message to queue")
            self.logger.error(e)

    def disconnect(self):
        """Close the queue and disconnect from the Queue Manager."""
        if self.queue:
            try:
                self.queue.close()
                self.logger.info("Queue closed")
            except pymqi.MQMIError as e:
                self.logger.error("Error closing queue")
                self.logger.error(e)
        if self.qmgr:
            try:
                self.qmgr.disconnect()
                self.logger.info("Disconnected from Queue Manager")
            except pymqi.MQMIError as e:
                self.logger.error("Error disconnecting from Queue Manager")
                self.logger.error(e)


