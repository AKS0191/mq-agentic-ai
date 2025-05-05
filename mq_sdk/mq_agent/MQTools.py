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

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from datetime import *

from mq_sdk.mq_agent.MQRequest import MQRequest
from mq_sdk.utilities.types import Message

from typing import Optional

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field

class ContactExternalAgentToolArgs(BaseModel):
    message: str = Field(description="The message that you want to send to the external agent.")
    agent_name: str = Field(description="The name of the agent that you want to contact within the network.")

class ContactExternalAgentTool(BaseTool):
    name: str = "contact_external_agent"
    description: str = "Contact an external agent in the network. You will be be notified when the external agent replies to your message."
    args_schema: Optional[ArgsSchema] = ContactExternalAgentToolArgs
    return_direct: bool = True

    def _run(
        self, 
        message:str, 
        agent_name:str, 
        config: RunnableConfig,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""        
        return self.contact_external_agent_func(
            message=message,
            agent_name=agent_name,
            config=config
        )
    
    # [TODO] - Add async support
    async def _arun(
        self, 
        message:str, 
        agent_name:str, 
        config: RunnableConfig,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""        
        return await self.contact_external_agent_func(
            message=message,
            agent_name=agent_name,
            config=config
    )

    def contact_external_agent_func(self, message, agent_name, config: RunnableConfig):        
        _config = config.get("configurable", {})        
        thread_id = _config.get("thread_id", None)    
        ccdt_path = _config.get("ccdt_path", None)
        try:
            msg = Message(
                message=message,
                thread_id=str(thread_id)
            )
        except Exception as e:
            print(f'>>>>>> Error: {e}')

        req = MQRequest(ccdt_path=ccdt_path)
        req.perform_connection()
        respone = req.put_and_wait_response(msg.model_dump_json())
        return respone