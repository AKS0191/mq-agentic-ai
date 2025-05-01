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

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import AnyMessage, add_messages # type: ignore
from datetime import *
from dotenv import load_dotenv
from mq_sdk.mq_agent.MQBaseAssistant import MQBaseAssistant
from agents.flights_searcher.tools import search_flights
import uuid
import json
load_dotenv()
from pydantic import BaseModel

class FlightInfo(BaseModel):
    airline: str
    departure_time: str
    departure_city: str
    flight_number: str
    duration: str
    arrival_time: str
    arrival_city: str
    fare_type: str
    price: str
    seats_left: str

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]    
    flight_info: str

class FlightSearcherAgent(MQBaseAssistant):    
    messages = []        
    tools = [search_flights]
    primary_assistant_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                        You are a capable flights searcher assistant.
                        You goal is to help the other assistants to find flights.
                        In order to search flights you need to be provided with:
                            1. departure city
                            2. arrival city
                            3. departure date
                            4. return date
                            5. number of passengers                                                                                                                       
                    """                                          
                ),
                ("placeholder", "{messages}"),
            ]
    ).partial()

    def __init__(self):
        super().__init__(
            ccdt_path="agents/flights_searcher/", 
            assistant_id=str(uuid.uuid4())
        )
        self.runnable = self.bind()    

    def on_state_change(self, msgObject: str):         
        try:            
            flight_infoJSON = json.loads(msgObject["Object"])            
            print(f'EventAssistant::on_message::{flight_infoJSON}')
            # should be better handle with singleton pattern for mutual exclusion
            self.reactive_state["flight_info"] = flight_infoJSON
        except Exception as e:
            print(f'EventAssistant::on_message::{e}')
             
    def custom_call(self, state: State, config: RunnableConfig):
        while True:                  
            result = self.runnable.invoke(state)            
            if not result.tool_calls and (
                not result.content
                or (isinstance(result.content, list) and not result.content[0].get("text"))
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages }
            else:
                break
        return {"messages": result}
        
    def bind(self):
        llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18", temperature=0)
        mq_chat_template = self.format_prompt_template(self.primary_assistant_prompt)      
        return mq_chat_template | self.bind_tools(llm, self.tools)
    
    def get_tools(self):
        return self.tools