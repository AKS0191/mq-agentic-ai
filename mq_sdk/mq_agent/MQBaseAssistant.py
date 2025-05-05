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

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from typing import List

from langchain_core.runnables import RunnableConfig
from mq_sdk.utilities.env import EnvStore
from mq_sdk.utilities.types import MQAgentInfo
from .MQPromptTemplate import MQPromptTemplate
from mq_sdk.utilities.constants import NETWORK_TYPE
from .MQTools import ContactExternalAgentTool


class MQBaseAssistant:
    def __init__(self, ccdt_path: str, assistant_id):
        self.ccdt_path = ccdt_path
        self.assistant_id = assistant_id
        self.env_store = EnvStore(ccdt_path, NETWORK_TYPE.OUTBOUND_NETWORK)
        
    def format_prompt_template(self, prompt: ChatPromptTemplate) -> MQPromptTemplate:
        agents_info: List[MQAgentInfo] = self.env_store.get_agents_info()        
        return MQPromptTemplate.format_prompt(agents_info, prompt)        

    def bind_tools(self, llm: BaseChatModel, tools: list):
        tools.append(ContactExternalAgentTool())
        return llm.bind_tools(tools)
