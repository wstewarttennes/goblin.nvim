r"""°°°
# State Schema 

## Review

In module 1, we laid the foundations! We built up to an agent that can: 

* `act` - let the model call specific tools 
* `observe` - pass the tool output back to the model 
* `reason` - let the model reason about the tool output to decide what to do next (e.g., call another tool or just respond directly)
* `persist state` - use an in memory checkpointer to support long-running conversations with interruptions
 
And, we showed how to serve it locally in LangGraph Studio or deploy it with LangGraph Cloud. 

## Goals

In this module, we're going to build a deeper understanding of both state and memory.

First, let's review a few different ways to define your state schema.
°°°"""
# |%%--%%| <RIhBtX5DoZ|hmbHK9Xwn6>

%%capture --no-stderr
%pip install --quiet -U langgraph

# |%%--%%| <hmbHK9Xwn6|kVaf5bqGRZ>
r"""°°°
## Schema

When we define a LangGraph `StateGraph`, we use a [state schema](https://langchain-ai.github.io/langgraph/concepts/low_level/#state).

The state schema represents the structure and types of data that our graph will use.

All nodes are expected to communicate with that schema.

LangGraph offers flexibility in how you define your state schema, accommodating various Python [types](https://docs.python.org/3/library/stdtypes.html#type-objects) and validation approaches!

## TypedDict

As we mentioned in Module 1, we can use the `TypedDict` class from python's `typing` module.

It allows you to specify keys and their corresponding value types.
 
But, note that these are type hints. 

They can used by static type checkers (like [mypy](https://github.com/python/mypy)) or IDEs to catch potential type-related errors before the code is run. 

But they are not enforced at runtime!
°°°"""
# |%%--%%| <kVaf5bqGRZ|P2S8TP8hm8>

from typing_extensions import TypedDict

class TypedDictState(TypedDict):
    foo: str
    bar: str

# |%%--%%| <P2S8TP8hm8|EfBwYrVTTR>
r"""°°°
For more specific value constraints, you can use things like the `Literal` type hint.

Here, `mood` can only be either "happy" or "sad".
°°°"""
# |%%--%%| <EfBwYrVTTR|NDNfc1eFTr>

from typing import Literal

class TypedDictState(TypedDict):
    name: str
    mood: Literal["happy","sad"]

# |%%--%%| <NDNfc1eFTr|4h4agR8Pmp>
r"""°°°
We can use our defined state class (e.g., here `TypedDictState`) in LangGraph by simply passing it to `StateGraph`.

And, we can think about each state key just a "channel" in our graph. 

As discussed in Module 1, we overwrite the value of a specified key or "channel" in each node.
°°°"""
# |%%--%%| <4h4agR8Pmp|LZAeEZGv7q>

import random
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END

def node_1(state):
    print("---Node 1---")
    return {"name": state['name'] + " is ... "}

def node_2(state):
    print("---Node 2---")
    return {"mood": "happy"}

def node_3(state):
    print("---Node 3---")
    return {"mood": "sad"}

def decide_mood(state) -> Literal["node_2", "node_3"]:
        
    # Here, let's just do a 50 / 50 split between nodes 2, 3
    if random.random() < 0.5:

        # 50% of the time, we return Node 2
        return "node_2"
    
    # 50% of the time, we return Node 3
    return "node_3"

# Build graph
builder = StateGraph(TypedDictState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

# Logic
builder.add_edge(START, "node_1")
builder.add_conditional_edges("node_1", decide_mood)
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)

# Add
graph = builder.compile()

# View
display(Image(graph.get_graph().draw_mermaid_png()))

# |%%--%%| <LZAeEZGv7q|oPOQrmCWdx>
r"""°°°
Because our state is a dict, we simply invoke the graph with a dict to set an initial value of the `name` key in our state.
°°°"""
# |%%--%%| <oPOQrmCWdx|OYxGbLRwBN>

graph.invoke({"name":"Lance"})

# |%%--%%| <OYxGbLRwBN|XTDYCRbstp>
r"""°°°
## Dataclass

Python's [dataclasses](https://docs.python.org/3/library/dataclasses.html) provide [another way to define structured data](https://www.datacamp.com/tutorial/python-data-classes).

Dataclasses offer a concise syntax for creating classes that are primarily used to store data.
°°°"""
# |%%--%%| <XTDYCRbstp|AllzhQQnoB>

from dataclasses import dataclass

@dataclass
class DataclassState:
    name: str
    mood: Literal["happy","sad"]

# |%%--%%| <AllzhQQnoB|7MXR7WgzeK>
r"""°°°
To access the keys of a `dataclass`, we just need to modify the subscripting used in `node_1`: 

* We use `state.name` for the `dataclass` state rather than `state["name"]` for the `TypedDict` above

You'll notice something a bit odd: in each node, we still return a dictionary to perform the state updates.
 
This is possible because LangGraph stores each key of your state object separately.

The object returned by the node only needs to have keys (attributes) that match those in the state!

In this case, the `dataclass` has key `name` so we can update it by passing a dict from our node, just as we did when state was a `TypedDict`.
°°°"""
# |%%--%%| <7MXR7WgzeK|eX6zwIbjUI>

def node_1(state):
    print("---Node 1---")
    return {"name": state.name + " is ... "}

# Build graph
builder = StateGraph(DataclassState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

# Logic
builder.add_edge(START, "node_1")
builder.add_conditional_edges("node_1", decide_mood)
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)

# Add
graph = builder.compile()

# View
display(Image(graph.get_graph().draw_mermaid_png()))

# |%%--%%| <eX6zwIbjUI|O5Z1VkprUE>
r"""°°°
We invoke with a `dataclass` to set the initial values of each key / channel in our state!
°°°"""
# |%%--%%| <O5Z1VkprUE|1fZKDsPUiI>

graph.invoke(DataclassState(name="Lance",mood="sad"))

# |%%--%%| <1fZKDsPUiI|cZbgCl1ivm>
r"""°°°
## Pydantic

As mentioned, `TypedDict` and `dataclasses` provide type hints but they don't enforce types at runtime. 
 
This means you could potentially assign invalid values without raising an error!

For example, we can set `mood` to `mad` even though our type hint specifies `mood: list[Literal["happy","sad"]]`.
°°°"""
# |%%--%%| <cZbgCl1ivm|9KdTq3eEBO>

dataclass_instance = DataclassState(name="Lance", mood="mad")

# |%%--%%| <9KdTq3eEBO|i7SsJTzu5h>
r"""°°°
[Pydantic](https://docs.pydantic.dev/latest/api/base_model/) is a data validation and settings management library using Python type annotations. 

It's particularly well-suited [for defining state schemas in LangGraph](https://langchain-ai.github.io/langgraph/how-tos/state-model/) due to its validation capabilities.

Pydantic can perform validation to check whether data conforms to the specified types and constraints at runtime.
°°°"""
# |%%--%%| <i7SsJTzu5h|5LjsrVPxIf>

from pydantic import BaseModel, field_validator, ValidationError

class PydanticState(BaseModel):
    name: str
    mood: Literal["happy", "sad"]

    @field_validator('mood')
    @classmethod
    def validate_mood(cls, value):
        # Ensure the mood is either "happy" or "sad"
        if value not in ["happy", "sad"]:
            raise ValueError("Each mood must be either 'happy' or 'sad'")
        return value

try:
    state = PydanticState(name="John Doe", mood="mad")
except ValidationError as e:
    print("Validation Error:", e)

# |%%--%%| <5LjsrVPxIf|vQnTqvSbXS>
r"""°°°
We can use `PydanticState` in our graph seamlessly. 
°°°"""
# |%%--%%| <vQnTqvSbXS|DpeRunFsUw>

# Build graph
builder = StateGraph(PydanticState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

# Logic
builder.add_edge(START, "node_1")
builder.add_conditional_edges("node_1", decide_mood)
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)

# Add
graph = builder.compile()

# View
display(Image(graph.get_graph().draw_mermaid_png()))

# |%%--%%| <DpeRunFsUw|tDhY5YM3KD>

graph.invoke(PydanticState(name="Lance",mood="sad"))

# |%%--%%| <tDhY5YM3KD|hSapQLj0Fr>


