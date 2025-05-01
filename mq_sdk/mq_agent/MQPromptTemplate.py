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

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from typing import List, Any

from mq_sdk.utilities.types import MQAgentInfo

class MQPromptTemplate(ChatPromptTemplate):

    @classmethod
    def format_prompt(cls, agents_info: List[MQAgentInfo], prompt: ChatPromptTemplate) -> ChatPromptTemplate:               
        """
            Format the prompt to include the agents information.
        """
        new_messages: List[Any] = []
        agent_template = cls.__get_agent_template(agents_info)
        for msg in prompt.messages:            
            if isinstance(msg, SystemMessagePromptTemplate):
                original_template = msg.prompt.template.strip()
                updated_template = original_template + agent_template                
                new_messages.append(("system", updated_template))
            else:                
                new_messages.append(msg)
               
        return ChatPromptTemplate.from_messages(new_messages).partial()
    
    @classmethod
    def __get_agent_template(cls, agents_info: List[MQAgentInfo]) -> str:
        """
            Get the agent template.
        """
        agent_template = """\n\n
        To achieve you goals you can delegate tasks to external agents available within your network.
        You can check the status of the delegated tasks. 
        When a delegated is completed, you will receive a reply.\n\n
        <NETWORK>\n
        <AGENTS_AVAILABLE>
       """
        for info in agents_info:
            agent_template += f"{info.agent_name}: {info.agent_description}\n"
        agent_template += "</AGENTS_AVAILABLE>\n\n"

        delegated_tasks = []
        agent_template += f"<DELEGATED_TASKS_STATUS> {delegated_tasks} </DELEGATED_TASKS_STATUS>\n"
        agent_template += "</NETWORK>"
        return agent_template

       