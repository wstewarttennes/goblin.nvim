import json
import logging
import os
import re
import asyncio
from typing import Dict, Any, List, Optional, Sequence, TypedDict
from langsmith import trace
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import OperationalError, connection
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_anthropic import ChatAnthropic
from langchain.tools import StructuredTool
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

from brain.jestor.lib.database import DatabaseManager
from brain.jestor.lib.cityflavor import CityFlavorQueryTool
from brain.providers import anthropic, openai, llama

LANGCHAIN_TRACING_V2 = True
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = "cityflavor-analysis"

logger = logging.getLogger(__name__)


class AnalyzeDataSchema(BaseModel):
    """Schema for the analyze_data tool arguments"""

    query_description: str


class AgentState(TypedDict):
    """Type definition for the agent's state"""

    messages: Sequence[Any]
    tool_calls: List[Dict[str, Any]]
    next_step: Optional[str]


class ToolRegistry:
    """Registry for managing tools with LangChain integration"""

    def __init__(self):
        self._tools = {}

    def register_tool(
        self, name: str, func, description: str, args_schema: type[BaseModel]
    ):
        """Register a tool using LangChain's StructuredTool"""
        self._tools[name] = StructuredTool.from_function(
            func=func, name=name, description=description, args_schema=args_schema
        )

    def get_tools(self) -> List[StructuredTool]:
        """Get all registered tools"""
        return list(self._tools.values())


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            # Initialize components
            self.tool_registry = ToolRegistry()
            self._register_default_tools()

            # Initialize AI provider based on configuration
            provider_name = os.environ.get("AI_PROVIDER", "anthropic")

            if provider_name.lower() == "anthropic":
                self.provider = anthropic.AnthropicProvider()
            elif provider_name.lower() == "openai":
                self.provider = openai.OpenAIProvider()
            elif provider_name.lower() == "llama":
                self.provider = llama.LlamaProvider()
            else:
                raise ValueError(f"Unsupported provider: {provider_name}")

            # Create and compile the workflow
            with trace(
                name="Graph Initialization", project_name=LANGCHAIN_PROJECT
            ) as tracer:
                graph = self._create_graph()
                if graph is None:
                    raise ValueError("Failed to create graph")

                logger.info("Validating the graph...")
                validation_result = graph.validate()
                logger.info(f"Graph validation result: {validation_result}")

                self.graph = graph
                self.app = self.graph.compile()
                logger.info("Graph compiled successfully")

        except Exception as e:
            logger.error("Error during ChatConsumer initialization", exc_info=True)
            raise

    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        try:
            logger.info("Starting graph creation...")

            if not hasattr(self, "provider") or self.provider is None:
                raise ValueError("AI provider not properly initialized")

            graph = StateGraph(AgentState)
            logger.info("StateGraph initialized")

            try:
                # Update the system prompt to be more explicit about tool usage
                prompt = ChatPromptTemplate.from_messages(
                    [
                        (
                            "system",
                            """You are an AI assistant with DIRECT access to a food vendor database through the analyze_city_flavor_data tool.

                    CRITICAL INSTRUCTIONS:
                    1. You MUST use the analyze_city_flavor_data tool for EVERY data-related question
                    2. NEVER say you don't have access to data
                    3. NEVER respond without using the tool for data queries
                    4. If the tool returns no data, explain that to the user but don't claim you can't access data
                    
                    Tool Usage Format:
                    <tool>analyze_city_flavor_data("your specific query")</tool>

                    Example Queries:
                    - <tool>analyze_city_flavor_data("Get total sales for Akita Sushi 1 from 2024-03-01")</tool>
                    - <tool>analyze_city_flavor_data("Show order count for downtown vendors today")</tool>
                    - <tool>analyze_city_flavor_data("Compare sales metrics for Fries First between yesterday and today")</tool>

                    After getting tool results:
                    1. Always explain the data in clear, natural language
                    2. Highlight key metrics and trends
                    3. Offer to analyze additional aspects if relevant
                    """,
                        ),
                        MessagesPlaceholder(variable_name="messages"),
                    ]
                )
                logger.info("Prompt template created successfully")
            except Exception as e:
                logger.error(f"Failed to create prompt template: {str(e)}")
                raise

            # Define the processing node
            async def process_message(state: AgentState) -> AgentState:
                """Process message node with tracing"""
                with trace(
                    name="Process Message Node", project_name=LANGCHAIN_PROJECT
                ) as node_tracer:
                    try:
                        # Analyze the input to ensure we're using the tool
                        user_message = state["messages"][-1].content
                        if any(
                            keyword in user_message.lower()
                            for keyword in [
                                "sales",
                                "revenue",
                                "orders",
                                "metrics",
                                "trends",
                                "performance",
                            ]
                        ):
                            # Format tool call if not already formatted
                            if not "<tool>" in user_message:
                                formatted_query = f'<tool>analyze_city_flavor_data("{user_message}")</tool>'
                                state["messages"].append(
                                    HumanMessage(content=formatted_query)
                                )

                        # Build complete response from stream
                        response_content = ""
                        async for chunk in self.provider.generate_response_stream(
                            state["messages"]
                        ):
                            response_content += chunk
                            await self.send(
                                json.dumps(
                                    {
                                        "type": "chat_message_chunk",
                                        "message": chunk,
                                        "is_complete": False,
                                    }
                                )
                            )

                        state["messages"].append(AIMessage(content=response_content))

                        # Check for tool calls
                        tool_match = re.search(
                            r"<tool>(.*?)\((.*?)\)</tool>", response_content
                        )
                        if tool_match:
                            tool_name = tool_match.group(1)
                            tool_args = {
                                "query_description": tool_match.group(2).strip("\"'")
                            }

                            with trace(
                                name="Tool Execution",
                                project_name=LANGCHAIN_PROJECT,
                                metadata={"tool_name": tool_name},
                            ):
                                result = await self._handle_city_flavor_data_analysis(
                                    **tool_args
                                )
                                state["messages"].append(
                                    HumanMessage(content=f"Tool result: {str(result)}")
                                )

                                # Get final response with streaming
                                final_content = ""
                                async for (
                                    chunk
                                ) in self.provider.generate_response_stream(
                                    state["messages"]
                                ):
                                    final_content += chunk
                                    await self.send(
                                        json.dumps(
                                            {
                                                "type": "chat_message_chunk",
                                                "message": chunk,
                                                "is_complete": False,
                                            }
                                        )
                                    )
                                state["messages"].append(
                                    AIMessage(content=final_content)
                                )

                        return state

                    except Exception as e:
                        logger.error(
                            f"Error in process_message: {str(e)}", exc_info=True
                        )
                        state["messages"].append(AIMessage(content=f"Error: {str(e)}"))
                        return state

            # Add the node to the graph
            graph.add_node("process_message", process_message)
            logger.info("Node 'process_message' added")

            # Set the entry point
            graph.set_entry_point("process_message")
            logger.info("Entry point set to 'process_message'")

            return graph

        except Exception as e:
            logger.error(f"Error creating graph: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to create graph: {str(e)}")

    async def connect(self):
        """Handle WebSocket connection setup"""
        try:
            await database_sync_to_async(self.test_db_connection)()
            await self.accept()
            await self.send(
                json.dumps({"type": "connection_status", "status": "connected"})
            )
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            await self.close()

    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            data = json.loads(text_data)
            message = data["message"]
            project = data["project"]
            provider = data["provider"]
            print(provider)
            print(project)
            print(message)

            if provider.lower() == "anthropic":
                self.provider = anthropic.AnthropicProvider()
            elif provider.lower() == "openai":
                self.provider = openai.OpenAIProvider()
            elif provider.lower() == "llama":
                self.provider = llama.LlamaProvider()
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            # Initialize state with system prompt
            system_prompt = f"""
                You are an AI assistant named GOBLIN. You have many tools to use. 
                Your current provider is {provider}.
                Your current project is {project}

            Your current tool list is:

            City Flavor Analysis: access to tools for analyzing food vendor data on the City Flavor platform


            """

            state = AgentState(
                messages=[
                    HumanMessage(content=system_prompt),
                    HumanMessage(content=message),
                ],
                tool_calls=[],
                next_step="process_message",
            )

            with trace(
                name="Chat Conversation",
                project_name=LANGCHAIN_PROJECT,
                metadata={
                    "channel_name": self.channel_name,
                    "message_type": "user_input",
                },
            ) as conversation_tracer:
                final_state = await self.app.ainvoke(
                    state,
                    config={
                        "recursion_limit": 10,
                        "metadata": {"session_id": self.channel_name},
                    },
                )

            # Send completion message
            await self.send(
                json.dumps(
                    {"type": "chat_message_chunk", "message": "", "is_complete": True}
                )
            )

        except Exception as e:
            logger.error("Message processing error", exc_info=True)
            logger.error(str(e), exc_info=True)
            await self.send(json.dumps({"type": "error", "message": str(e)}))

    def _register_default_tools(self):
        """Register default tools"""
        try:
            logger.info("Registering default tools...")
            self.tool_registry.register_tool(
                name="analyze_city_flavor_data",
                func=self._handle_city_flavor_data_analysis,
                description="""
                Analyze food vendor program data:
                - Orders: Search by date, vendor, location
                - Vendors: Get performance metrics
                - Locations: View activity trends
                - Shifts: Check schedules and metrics
                """,
                args_schema=AnalyzeDataSchema,
            )
            logger.info("Tool 'analyze_city_flavor_data' registered successfully")
        except Exception as e:
            logger.error(f"Error registering tools: {str(e)}", exc_info=True)

    async def _handle_city_flavor_data_analysis(
        self, query_description: str
    ) -> Dict[str, Any]:
        """Handler for analyzing city flavor data"""
        with trace(
            name="City Flavor Analysis",
            project_name=LANGCHAIN_PROJECT,
            metadata={"query": query_description},
        ) as analysis_tracer:
            try:
                db_manager = DatabaseManager()
                city_flavor_query_tool = CityFlavorQueryTool(db_manager)
                results = await city_flavor_query_tool.analyze_data(query_description)

                if results["status"] == "success":
                    return {
                        "status": "success",
                        "data": results.get("data", []),
                        "summary": results.get("summary", {}),
                        "message": "Analysis completed successfully",
                    }
                else:
                    return {
                        "status": "error",
                        "message": results.get("message", "Unknown error"),
                    }
            except Exception as e:
                logger.error("Analysis error", exc_info=True)
                return {"status": "error", "message": str(e)}

    def test_db_connection(self):
        """Test database connection"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except OperationalError as e:
            logger.error(f"Database connection test failed: {str(e)}")
            raise
