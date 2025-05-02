
# IBM MQ for LLM Agentic Applications
This repository demonstrates the integration of IBM MQ with LLM Agentic Applications to support event-driven agents and Distributed Multi-Agent Systems (DMAS), an advanced evolution of traditional multi-agent systems. At the moment we have only integrated with LangGraph, a popular open-source agentic AI framework, to demonstrate our vision for MQ as async message broker. However, we hope to see this work lead to integrations with existing protocols (A2A, ACP, MCP), other agentic frameworks, and use cases.

# MQ for Agent State Management
The `primary_agent` is a LangGraph-based example illustrating how IBM MQ enables real-time agent state updates. This feature leverages the MQ Publish/Subscribe pattern, ideal for scenarios where an agent’s state must reflect external events. To enable this:
- The agent’s `env.json` `STATE_NETWORK` configuration specifies the IBM MQ topic for receiving state updates.
- A callback method (`on_state_change`) processes these updates within the agent, ensuring dynamic state management.

# MQ for Distributed Agents
The `primary_agent` and `flights_searcher` agents demonstrate how IBM MQ supports Distributed Multi-Agent Systems (DMAS). 
DMAS extends traditional multi-agent systems by allowing agents to operate asynchronously on independent networks, collaborating through reliable message exchange via IBM MQ. 
Each agent’s network configuration, defined in `env.json`, includes `OUTBOUND_NETWORK` for delegating tasks to other agents based on their `AGENT_DESCRIPTION` and `INBOUND_NETWORK` for receiving messages from other agents via a specified queue. 
Each message object exchanged between agents encapsulates a unique `thread_id`, enabling agents to track and retrieve the conversation history. This `thread_id` is included in the message payload and used by each agent logic to maintain context across interactions. 

To enable DMAS, the following features are provided:
- Network Configuration:
 1. `OUTBOUND NETWORK`: The `OUTBOUND_NETWORK`, defined in each agent’s `env.json` configuration file, enables agents to securely delegate tasks to other agents in the Distributed Multi-Agent System (DMAS) by specifying IBM MQ connection details and target agent roles. It consists of one or more `MQ_ENDPOINTS`, each defining a queue for sending messages, along with authentication credentials (`APP_USER`, `APP_PASSWORD`) to ensure secure communication. The `AGENT_DESCRIPTION` field within each `MQ_ENDPOINT` specifies the role or task of the target agent (e.g., “Handles flight search and booking requests”), allowing the sending agent to route messages to the appropriate agent based on its role. For example, the `primary_agent` may send a flight search request to a queue associated with the `flights_searcher` agent’s `AGENT_DESCRIPTION`. Dynamic queues, configured via `MODEL_QUEUE_NAME` and `DYNAMIC_QUEUE_PREFIX`, support temporary reply queues for asynchronous responses.

  ```
  "OUTBOUND_NETWORK": {
    "MQ_ENDPOINTS": [
        "HOST": "MQ host",
        "PORT": "MQ port",
        "CHANNEL": "MQ Channel",
        "QMGR": "QM name",
        "APP_USER": "authorised user",
        "APP_PASSWORD": "authorised user password",
        "QUEUE_NAME": "queue name",
        "MODEL_QUEUE_NAME": "model queue name eg: DEV.APP.MODEL.QUEUE",
        "DYNAMIC_QUEUE_PREFIX": "dynamic queue prefix eg. APP.REPLIES.*"
        "AGENT_DESCRIPTION": "External Agent description",
        "AGENT_NAME": "External Agent name"   
    ]
  }
  ```

  2. `INBOUND NETWORK`: The `INBOUND_NETWORK`, defined in each agent’s `env.json` configuration file, enables agents to receive and process messages from other agents in the Distributed Multi-Agent System (DMAS) by specifying IBM MQ connection details for queues or topics. Agents monitor their `INBOUND_NETWORK` to asynchronously process incoming messages. For example, the `flights_searcher` agent listens to the `FLIGHT_REQUESTS` queue to handle flight search requests delegated by the `primary_agent`.
  ```
    "INBOUND_NETWORK": {
      "MQ_ENDPOINTS" : [
        "HOST": "MQ host",
        "PORT": "MQ port",
        "CHANNEL": "MQ Channel",
        "QMGR": "QM name",
        "APP_USER": "authorised user",
        "APP_PASSWORD": "auhtorised user password",
        "QUEUE_NAME": "queue name"
      ]
    }  
  ```
  Secure communication can be enabled by including within each `MQ_ENDPOINTS` the following fields:
  ```
  CIPHER_SUITE - If present in the env.json, TLS Cipher specification to use
  KEY_REPOSITORY - Path to the keystore .kbd and .sth files. If running on Apple Silicon then this will the path to the queue manager's exported .pem. If present in the env.json, TLS is enabled - this is on the app side.
  ```
- Networking tools: a collection of pre-built networking tools is provided, enabling seamless message transmission between agents within the `OUTBOUND_NETWORK`. These tools facilitate reliable and secure communication, ensuring messages are routed effectively across the network.
- Listener incoming messages: ability to initiate an asynchronous agent workflow upon receiving a new message in the `INBOUND_NETWORK`.

## Getting Started
These python samples are based on https://dsuch.github.io/pymqi/
and have been tested with python 3.10.12,3.11.9 and 3.12.5

Python PyMQI library uses the IBM MQ C client libraries through the MQI interface.

The library needs to be compiled with a C compiler which you need to have installed in your development environment.

For example, on MacOS we used `XCode`, on Windows the `Desktop development with C++` module inside Visual Studio and on Ubuntu the `gcc` GNU Compiler Collection.

Install/unzip IBM MQ client

### Mac

[IBM MQ MacOS toolkit for developers download](https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/mactoolkit/)

Add
`/opt/mqm/bin` and
`/opt/mqm/samp/bin`, to the PATH by editing `/etc/paths`

execute the following command:
`export DYLD_LIBRARY_PATH=/opt/mqm/lib64`

### Windows

[Windows MQ redist client download](https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist/)

### Linux Ubuntu

[Linux MQ redist client download](https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist/)

For installation instructions please go to 
#### [linux installation](../../mq-dev-patterns/installationDocs/linuxUbuntu-installationSteps.md)

### Clone the repository
```
git clone git@github.com:ibm-messaging/mq-agentic-ai.git
cd mq-agentic-ai
```

### Install requirements
```
pip install -r requirements.txt
```

### Set up the Queue Manager
You might need to set up a Queue Manage before running these samples.
To get your MQ server set up, check out [Ready, Set, Connect](https://developer.ibm.com/series/mq-ready-set-connect/).
The Queue Manager configuration to run these samples can be obtained by following the commands within the `qm_set_up.txt` file.

### Run the code
Set `MQ_HOST_IP`, `MQ_HOST_PORT`, and `APP_USER_PASSWORD` within each agent `env.json`.

#### MQ For Agent State
Start the primary agent
```
python start_primary_agent.py
```
In a separate terminal (ensure Link MQ Toolkit libraries are exported), launch the price emitter to simulate dynamic flight price updates as state changes. Querying the primary agent for flight prices at various conversation stages will yield different prices, as the agent's state is updated in the background based on the price emitter's updates.
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
#### MQ For Distributed Multi-Agent Systems (DMAS)
Launch the primary agent and request a new flight booking. The request will be delegated to the FlightSearchAgent, which operates on its own resource and network, handling and responding to the booking request when available. Even if the FlightSearchAgent is up or down, the booking request remains secure and reliable, as IBM MQ facilitates asynchronous message exchange.
```
python start_primary_agent.py
```
Start the flight searcher agent on a new terminal tab
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

## Want to learn more?
Keen to learn more about IBM MQ samples and built applications? Check [mq-dev-patterns](https://github.com/ibm-messaging/mq-dev-patterns).


## Issue Support

The code in this repository is provided and maintained on a community basis, and is not covered by any IBM commercial support agreement or warranty.

For enhancements, issues and fixes you are welcome raise an issue against this repository so that it may be considered. 
