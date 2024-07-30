from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Optional
import os
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI


load_dotenv()


# model = ChatOpenAI(model="gpt-4o")
# messages = [
#     SystemMessage(content="Translate the following from English into Italian"),
#     HumanMessage(content="hi!"),
# ]
# parser = StrOutputParser()
#
# system_template = "Translate the following into {language}:"
# prompt_template = ChatPromptTemplate.from_messages(
#     [("system", system_template), ("user", "{text}")]
# )
# chain = prompt_template | model | parser
#
# chain.invoke({"language": "italian", "text": "hi"})


llm = ChatOpenAI(model="gpt-3.5-turbo-0125")


class Joke(BaseModel):
    """Joke to tell user."""

    buffer: str = Field(description="The setup of the joke")
    punchline: str = Field(description="The punchline to the joke")
    rating: Optional[int] = Field(description="How funny the joke is, from 1 to 10")


structured_llm = llm.with_structured_output(Joke)

for chunk in structured_llm.stream("Tell me a joke about cats"):
    print(chunk)


# tool = TavilySearchResults()
#
#
# tool.invoke({"query": "What happened in the latest burning man floods"})
#
#
# instructions = """You are an assistant."""
# base_prompt = hub.pull("langchain-ai/openai-functions-template")
# prompt = base_prompt.partial(instructions=instructions)
# llm = ChatOpenAI(temperature=0)
# tavily_tool = TavilySearchResults()
# tools = [tavily_tool]
# agent = create_openai_functions_agent(llm, tools, prompt)
# agent_executor = AgentExecutor(
#     agent=agent,
#     tools=tools,
#     verbose=True,
# )
