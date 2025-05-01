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
import pymqi
import math
import logging
from mq_sdk.utilities.constants import NETWORK_TYPE

class MQResponse():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    def __init__(self, ccdt_path: str):        
        self.envStore = EnvStore(
            ccdt_path=ccdt_path,
            network_type=NETWORK_TYPE.INBOUND_NETWORK
        )
        self.envStore.setEnv()

        self.MQDetails = {}
        self.credentials = {
            self.envStore.USER: self.envStore.getEnvValue(self.envStore.APP_USER),
            self.envStore.PASSWORD: self.envStore.getEnvValue(self.envStore.APP_PASSWORD)
        }

        self.buildMQDetails()

        self.logger.info('Credentials are set')
        #logger.info(credentials)

        #conn_info = "%s(%s)" % (MQDetails[self.envStore.HOST], MQDetails[self.envStore.PORT])
        self.conn_info = self.envStore.getConnection(self.envStore.HOST, self.envStore.PORT)

        self.qmgr = None
        self.queue = None

    
    def buildMQDetails(self):
        for key in [self.envStore.QMGR, self.envStore.QUEUE_NAME, self.envStore.CHANNEL, self.envStore.HOST,
                    self.envStore.PORT, self.envStore.KEY_REPOSITORY, self.envStore.CIPHER, self.envStore.BACKOUT_QUEUE]:
            self.MQDetails[key] = self.envStore.getEnvValue(key)


    def perform_connection(self):
        self.qmgr = self.connect()


    def perform_get(self):
        if(self.qmgr):
            self.queue = self.getQueue(self.MQDetails[self.envStore.QUEUE_NAME], True)    
        
        if(self.queue):
            md, msgObject = self.getMessages(self.qmgr)
            return md, msgObject
            self.queue.close()
        
        if(self.qmgr):
            self.qmgr.disconnect()
        
        self.logger.info("Application is closing")


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


    def getQueue(self,queueName, forInput):
        self.logger.info('Connecting to Queue')
        try:
            # Works with single call, but object Descriptor
            # provides other options
            # q = pymqi.Queue(qmgr, MQDetails[self.envStore.QUEUE_NAME])
            q = pymqi.Queue(self.qmgr)
            od = pymqi.OD()
            od.ObjectName = queueName

            if (forInput):
                odOptions = pymqi.CMQC.MQOO_INPUT_AS_Q_DEF
            else:
                od.ObjectType = pymqi.CMQC.MQOT_Q
                odOptions = pymqi.CMQC.MQOO_OUTPUT

            q.open(od, odOptions)
            return q

        except pymqi.MQMIError as e:
            self.logger.error("Error getting queue")
            self.logger.error(e)
            return None
        

    def getMessages(self,qmgr):
        self.logger.info('Attempting gets from Queue')
        # Message Descriptor
        # Get Message Options
        gmo = pymqi.GMO()
        gmo.Options = pymqi.CMQC.MQGMO_WAIT | pymqi.CMQC.MQGMO_FAIL_IF_QUIESCING | pymqi.CMQC.MQGMO_SYNCPOINT
        gmo.WaitInterval = 5000  # 5 seconds

        keep_running = True
        
        while keep_running:
            backoutCounter = 0   
            ok = True
            msgObject = None

            try:
                # Reset the MsgId, CorrelId & GroupId so that we can reuse
                # the same 'md' object again.
                md = pymqi.MD()
                md.MsgId = pymqi.CMQC.MQMI_NONE
                md.CorrelId = pymqi.CMQC.MQCI_NONE
                md.GroupId = pymqi.CMQC.MQGI_NONE
                
                # Wait up to to gmo.WaitInterval for a new message.
                message = self.queue.get(None, md, gmo)
                backoutCounter = md.BackoutCount             

                # Process the message here..
                msgObject = json.loads(message.decode())            
                self.logger.info('Have message from Queue')
                self.logger.info(msgObject)    
                return md, msgObject

            except pymqi.MQMIError as e:
                if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE:
                    # No messages, that's OK, we can ignore it.
                    ok = True
                else:
                    # Some other error condition.
                    ok = False        

            except (UnicodeDecodeError, ValueError) as e:
                self.logger.info('Message is not valid json')
                self.logger.info(e)
                self.logger.info(message)
                ok = False
                continue

            except KeyboardInterrupt:
                self.logger.info('Have received a keyboard interrupt')
                keep_running = False

            except:
                ok = False


            if ok == True:
                #Commiting 
                qmgr.commit()            
            elif ok == False:
                keep_running=self.rollback(qmgr, md, msgObject, backoutCounter)        

    
    def respondToRequest(self, message, md):
        # Create a response message descriptor with the CorrelId
        # set to the value of MsgId of the original request message.
        response_md = pymqi.MD()
        response_md.CorrelId = md.CorrelId
        response_md.MsgId = md.MsgId
        response_md.Format = pymqi.CMQC.MQFMT_STRING
        response_md.ReplyToQ= md.ReplyToQ
        print(f'responding to request {md.ReplyToQ}')
        msgReply = {
            'reply_from_external_assistant': message,            
        }

        replyQueue = self.getQueue(response_md.ReplyToQ, False)                

        try:
            replyQueue.put(self.envStore.stringForVersion(json.dumps(msgReply)), response_md)
            return True
        except:
            #Roll back on exception
            return False
        
    
    def rollback(self, qmgr , md, msg, backoutCounter):
        # get the backout queue from the Environment --> fix this
        BACKOUT_QUEUE = self.MQDetails[self.envStore.BACKOUT_QUEUE]
    
        ok = False 

        # if the backout counter is greater than 5
        # handle possible poisoning message scenario
        if (backoutCounter >= 5):
            self.logger.info("POSIONING MESSAGE DETECTED! ")
            self.logger.info("REDIRECTING THE MESSAGE TO THE BACKOUT QUEUE " + str(BACKOUT_QUEUE))
            backoutQueue = self.getQueue(BACKOUT_QUEUE, False)

            try:
                msg = self.envStore.stringForVersion(json.dumps(msg))
                backoutQueue.put(msg,md)            
                qmgr.commit()                        
                ok = True
                self.logger.info("Message sent to the backout queue" + str(BACKOUT_QUEUE))
            except:
                self.logger.info("Error on redirecting the message")
                ok = False

        else:        

            try:
                qmgr.backout()            
                ok = True
            except:
                self.logger.error("Error on rollback")
                ok = False
                
        return ok
        
    def performCalc(self, n):
        sqRoot = math.floor(math.sqrt(n))
        a = []
        i = 2
        j = 1

        while (sqRoot <= n and i <= sqRoot):
            if (0 == n % i):
                a.append(i)
                n /= i
            else:
                j = 2 if i > 2 else 1
                i += j
        return a
