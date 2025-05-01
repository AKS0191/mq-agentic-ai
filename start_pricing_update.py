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

from flights_pricing.flight_emitter import FlightEmitter
from flights_pricing.flight_reader import FlightReader, FlightInfo
import time

MQ = "agents/primary_agent/"

if __name__ == "__main__":
    reader:FlightReader = FlightReader()
    emitter:FlightEmitter = FlightEmitter(MQ)
    last_flights:list[FlightInfo] = None
    while True:    
        flights:list[FlightInfo] = reader.generate_flight_info()    
        print(f'>>>> {flights}')
        some_change = False
        if last_flights is None:
            last_flights = flights
            continue
        if len(flights) != len(last_flights):
                continue
        for i in range(len(flights)):
            lflight:FlightInfo = last_flights[i]
            fight:FlightInfo = flights[i]
            some_changes = lflight.price != fight.price or lflight.seats_left != fight.seats_left
            print(f'>>> Something is changed: {some_changes}')
            if some_changes or True:
                last_flights = flights
                emitter.publishMessage(flights[i].model_dump_json()) 
        time.sleep(10)







