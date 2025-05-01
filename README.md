
# IBM MQ for LLM Agentic Applications
This repo shows how IBM MQ can be used within LLM Agentic Applications for event-driven agents and Distributed Multi-Agent Systems (DMAS), an evolution of traditional multi-agent systems. For the pure purpose of this sample, LangGraph was chosen as the agentic framework to illustrate its functionality.

## MQ For Agents' State: 
`primary_agent` is a LangGraph agent example showing how MQ can be used to update an agent's state in real-time.
This capability uses the Pub/Sub MQ pattern and is relevant in use cases requiring the agent' state to be updated based on external events.
To enable this feature, the agent's configuration `env.json` file specifies the IBM MQ topic for receiving state updates. A callback method (`on_state_change`) handles the state changes within the agent.

## MQ For Distribued Agents
`primary_agent` and `flights_searcher` are two agents showing an example of how IBM MQ can be used by Distributed Multi-Agent Systems (DMAS). 
DMAS are an evolution of common multi-agent systems in which each agent runs in its own network asynchronously and cooperate & collaborate with other agents by exchanging messages reliably via IBM MQ.
In order to enable DMAS the following features are provided in this repo (by inheriting `MQBaseAssistant` into your agent class):
- network definition:
  1. An agent can securely exchange messages to another agent by defining the OUTBOUND_NETWORK within its `env.json` file.

  ```
  "OUTBOUND_NETWORK": {
    "MQ_ENDPOINTS": [
        "HOST": "MQ host",
        "PORT": "MQ port",
        "CHANNEL": "MQ Channel",
        "QMGR": "QM name",
        "APP_USER": "authorised user",
        "APP_PASSWORD": "auhtorised user password",
        "QUEUE_NAME": "queue name",
        "MODEL_QUEUE_NAME": "model queue name eg: DEV.APP.MODEL.QUEUE",
        "DYNAMIC_QUEUE_PREFIX": "dynamic queue prefix eg. APP.REPLIES.*"
        "AGENT_DESCRIPTION": "External Agent description",
        "AGENT_NAME": "External Agent name"   
    ]
  }
  ```

  2. An agent can be listening for incoming messages from other agents by defining INBOUND_NETWOKRK within its `env.json` file:
  ```
    "INBOUND_NETWORK": {
      "MQ_ENDPOINTS" : [
        "HOST": "MQ host",
        "PORT": "MQ port",
        "CHANNEL": "MQ Channel",
        "QMGR": "QM name",
        "APP_USER": "authorised user",
        "APP_PASSWORD": "auhtorised user password",
        "QUEUE_NAME": "queue name",
        "MODEL_QUEUE_NAME": "model queue name eg: DEV.APP.MODEL.QUEUE",
        "DYNAMIC_QUEUE_PREFIX": "dynamic queue prefix eg. APP.REPLIES.*"
      ]
    }
  ```
- networking tools: set of tools bounded into an agent to permit messages to flow from one agent to another within the OUTBOUND_NETWORK
- listener incoming messages: capability to start an async agent workflow when a new message arrives in the INBOUND_NETWOKRK

### Install MQ Toolkit
`https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/mactoolkit/`
Add locations of the bin directories /opt/mqm/bin and /opt/mqm/samp/bin to the PATH by editing /etc/paths 

### Link MQ Toolkit libs
```
export MQ_INSTALLATION_PATH=/opt/mqm
export LD_LIBRARY_PATH=/opt/mqm/lib64
export DYLD_LIBRARY_PATH=/opt/mqm/lib64
```

### Clone this repository
```
git clone https://github.ibm.com/FrancescoRinaldi/agentic-mq
cd agentic-mq
```

### Install requirements
```
pip install -r requirements.txt
```

### Queue Manager set up:
You might need to prepare the queue manager first. 
To run these examples, the Queue Manager can be configured following the commands within the `qm_set_up.txt` file.

### Run the code
Set `MQ_HOST_IP`, `MQ_HOST_PORT`, and `APP_USER_PASSWORD` within each agent `env.json`.

#### MQ For Agent State
Start the primary agent
```
python start_primary_agent.py
```
In another terminal (rememver to export Link MQ Toolkit libs) start the price emitter to simulate dynamic flights prices as a state updates. By asking to the primary agent the flight price at different stage of the conversation it will result in different prices provided back as a reply because the agent state is updated in the background according to the udaptes sent by the price emitter.
```
python start_pricing_update.py
```

Example Output Primary Agent:
```
Assistant: Hello! How can I assist you today?

User: whats the latest price?

Assistant: The latest price for your tracked flight (Flight FR5678) from Newcastle to Faro on May 11, 2025, is £82. There are 3 seats left. If you need any further assistance, feel free to ask!

User: whats the latest price?

Assistant: The latest price for your tracked flight (Flight FR5678) from Newcastle to Faro on May 11, 2025, is £151. There are 3 seats left. If you have any other questions or need assistance, just let me know!
```
#### MQ For Distribued Agent
Start the primary agent and ask for a new flight booking. You will notice that this request will be delegated to the FlightSearchAgent which is running on its own resource&network and it will handle and reply to the incominc flight booking request whenever available. Regardless of the up/down state of FlightSearchAgent the the flight booking request won't be lost as IBM MQ is used to exchange async messages in a relibale and secure way.
```
python start_primary_agent.py
```
Start the flight searcher agent on a fresh terminal tab
```
python start_flight_researcher.py

```

Example Output:
```
Assistant: Hello! How can I assist you today?

User: I would like to book a new flight, thanks

Networking Operations: [ 
  - PrimaryAgent triggers FlightSearchAgent by sending a message into the FlightSearchAgent INBOUND_NETWORK queue.
  - FlightSearchAgent receives: {"message":"Please search for a new flight for the user.","thread_id":"00a97aab-23a4-4509-a156-71736f2747d0","mqmd":null}
  - FlightSearchAgent replies by sending a message back to FlightSearchAgent reply queue: {'reply_from_external_assistant': 'I need the following details to search for a flight:\n\n1. Departure city\n2. Arrival city\n3. Departure date\n4. Return date\n5. Number of passengers\n\nPlease provide this information.'}
  - PrimaryAgent reads the FlightSearchAgent's reply
]

Assistant: I need a few details to help you find a new flight:
1. Departure city
2. Arrival city
3. Departure date
4. Return date (if applicable)
5. Number of passengers

Please provide this information!

User: from stanstead to milan, from 16th of May to 18th, no return, 2 passengers, thanks

Networking Operations: [ 
  - PrimaryAgent triggers FlightSearchAgent by sending a message into the FlightSearchAgent INBOUND_NETWORK queue.
  - FlightSearchAgent receives: {"message":"Search for a flight from Stansted to Milan on May 16th for 2 passengers, one-way.","thread_id":"00a97aab-23a4-4509-a156-71736f2747d0","mqmd":null}
  - FlightSearchAgent replies by sending a message back to FlightSearchAgent reply queue: {'reply_from_external_assistant': 'I found a flight for you! \n\n- **Flight Number:** RK679\n- **Departure City:** Stansted\n- **Arrival City:** Milan\n- **Departure Date:** May 16th\n- **Passengers:** 2 (one-way)\n\nIf you need any further assistance or details, feel free to ask!'}
  - PrimaryAgent reads the FlightSearchAgent's reply
]

Assistant: I found a flight for you!

- **Flight Number:** RK679
- **Departure City:** Stansted
- **Arrival City:** Milan
- **Departure Date:** May 16th
- **Passengers:** 2 (one-way)

If you need any further assistance or details, feel free to ask!
```
## Issue Support

The code in this repository is provided and maintained on a community basis, and is not covered by any IBM commercial support agreement or warranty.

For enhancements, issues and fixes you are welcome raise an issue against this repository so that it may be considered. 
