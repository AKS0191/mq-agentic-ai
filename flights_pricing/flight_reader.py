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

from random import randint
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

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

class FlightReader:
    def generate_flight_info(self) -> list[FlightInfo]:
        return [
            FlightInfo(
                airline="Ryanair",
                departure_time="2025-05-10T10:00:00Z",
                departure_city="Newcastle",
                flight_number="FR1234",
                duration="2h 30m",
                arrival_time="2025-05-10T12:30:00Z",
                arrival_city="Faro",
                fare_type="Economy",
                price=str(randint(50, 200)),
                seats_left="5"
            ),
            FlightInfo(
                airline="Ryanair",
                departure_time="2025-05-11T14:00:00Z",
                departure_city="Newcastle",
                flight_number="FR5678",
                duration="2h 30m",
                arrival_time="2025-05-11T16:30:00Z",
                arrival_city="Faro",
                fare_type="Economy",
                price=str(randint(50, 200)),
                seats_left="3"
            )
        ]          

    

 