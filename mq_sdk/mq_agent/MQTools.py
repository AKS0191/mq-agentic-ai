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

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from datetime import *

from mq_sdk.mq_agent.MQRequest import MQRequest
from mq_sdk.utilities.types import Message


@tool
def contact_external_agent(message, agent_name, config: RunnableConfig):
    """
        Contact an external agent in the network. You will be be notified when the external agent replies to your message. 

        Args:
            message: The message that you want to send to the external agent.
            agent_name: The name of the agent that you want to contact within the network.
        Returns:
            The response from the external agent.
    """
    print(f'Contacting External Agent: {agent_name}')
    _config = config.get("configurable", {})
    thread_id = _config.get("thread_id", None)    
    try:
        msg = Message(
            message=message,
            thread_id=str(thread_id)
        )
    except Exception as e:
        print(f'>>>>>> Error: {e}')

    req = MQRequest(ccdt_path="agents/primary_agent/")
    req.perform_connection()
    respone = req.put_and_wait_response(msg.model_dump_json())
    return respone