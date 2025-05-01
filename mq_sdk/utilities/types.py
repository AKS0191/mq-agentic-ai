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

from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import Optional
from pymqi import MD
from datetime import *

class MQAgentInfo(BaseModel):    
    agent_name: str = Field(..., alias="AGENT_NAME")
    agent_description: str = Field(..., alias="AGENT_DESCRIPTION")
    
    def info(self) -> str:
        return f"{self.agent_name}({self.agent_description})"
    
class MQAgentMessage(BaseModel):
    message: str
    sender: str
    receiver: str
    timestamp: datetime

class Message(BaseModel):
    message: str
    thread_id: str
    mqmd: Optional[MD] = None

    @field_validator('mqmd')
    def check_mqmd(cls, v):
        if v is not None and not isinstance(v, MD):
            raise ValueError(f"mqmd must be None or pymqi.MD, got {type(v)}")
        return v

    model_config = ConfigDict(arbitrary_types_allowed=True)