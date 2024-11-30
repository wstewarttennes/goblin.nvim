import json
import logging
import os
from typing import AsyncGenerator, Dict, Any, List, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import OperationalError

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_anthropic import ChatAnthropic
from langchain.tools import StructuredTool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_executor import ToolExecutor
from typing import TypedDict, Annotated, Sequence
import operator

# Configure logging
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """Type definition for the agent's state"""
    messages: Sequence[Any]
    tools: List[StructuredTool]
    tool_results: List[Dict[str, Any]]

class ToolRegistry:
    """Registry for managing tools with LangChain integration"""
    def __init__(self):
        self._tools = {}
    
    def register_tool(self, name: str, func, description: str, args_schema: Dict[str, Any]):
        """Register a tool using LangChain's StructuredTool"""
        self._tools[name] = StructuredTool.from_function(
            func=func,
            name=name,
            description=description,
            args_schema=args_schema
        )
    
    def get_tools(self) -> List[StructuredTool]:
        """Get all registered tools"""
        return list(self._tools.values())

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            # Initialize components
            self.db_manager = DatabaseManager()
            self.city_flavor_query_tool = CityFlavorQueryTool(self.db_manager)
            self.tool_registry = ToolRegistry()
            self._register_default_tools()
            
            # Initialize LangChain components
            self.model = ChatAnthropic(
                model="claude-3-opus-20240229",
                anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
                streaming=True
            )
            
            # Create the workflow graph
            self.workflow = self._create_workflow()
            
        except Exception as e:
            logger.error("Error during ChatConsumer initialization", exc_info=True)
            raise

    def _register_default_tools(self):
        """Register default tools with improved LangChain integration"""
        self.tool_registry.register_tool(
            name="analyze_city_flavor_data",
            func=self._handle_city_flavor_data_analysis,
            description="""
            Analyze data from the food vendor program database. You can analyze:
            - Orders: Search by date, vendor, or location
            - Vendors: Get performance metrics and history
            - Locations: View activity and trends
            - Shifts: Check schedules and performance
            """,
            args_schema={
                "query_description": str
            }
        )

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Define the system prompt
        system_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI assistant with access to various tools. {tool_descriptions}"),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Define chain for generating responses
        chain = system_prompt | self.model | StrOutputParser()
        
        # Tool execution node
        tool_executor = ToolExecutor(self.tool_registry.get_tools())
        
        # Define nodes
        def should_use_tool(state: AgentState) -> bool:
            """Determine if the last message indicates tool usage"""
            if not state["messages"]:
                return False
            last_message = state["messages"][-1].content
            return "<tool>" in last_message and "</tool>" in last_message

        def call_tool(state: AgentState) -> AgentState:
            """Execute the tool and update state"""
            last_message = state["messages"][-1].content
            # Extract tool call using the existing _extract_tool_call logic
            tool_call = self._extract_tool_call(last_message)
            if tool_call:
                result = tool_executor.execute(tool_call.name, tool_call.arguments)
                state["tool_results"].append(result)
                state["messages"].append(AIMessage(content=str(result)))
            return state

        def generate_response(state: AgentState) -> AgentState:
            """Generate AI response"""
            response = chain.invoke({
                "messages": state["messages"],
                "tool_descriptions": "\n".join(t.description for t in state["tools"])
            })
            state["messages"].append(AIMessage(content=response))
            return state

        # Add nodes to graph
        workflow.add_node("generate_response", generate_response)
        workflow.add_node("call_tool", call_tool)
        
        # Add edges
        workflow.add_edge("generate_response", "call_tool", should_use_tool)
        workflow.add_edge("call_tool", "generate_response")
        workflow.add_edge("generate_response", END, operator.not_)
        
        return workflow

    async def connect(self):
        """Handle WebSocket connection setup"""
        try:
            await database_sync_to_async(self.test_db_connection)()
            await self.accept()
            await self.send(json.dumps({
                'type': 'connection_status',
                'status': 'connected'
            }))
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            await self.close()

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message = data['message']
            
            # Initialize state
            state = AgentState(
                messages=[HumanMessage(content=message)],
                tools=self.tool_registry.get_tools(),
                tool_results=[]
            )
            
            # Run the workflow
            async for step in self.workflow.astream(state):
                if "messages" in step:
                    last_message = step["messages"][-1]
                    await self.send(json.dumps({
                        'type': 'chat_message_chunk',
                        'message': last_message.content,
                        'is_complete': False
                    }))
                
                if "tool_results" in step and step["tool_results"]:
                    last_result = step["tool_results"][-1]
                    await self.send(json.dumps({
                        'type': 'tool_status',
                        'status': 'completed',
                        'result': last_result
                    }))
            
            # Send completion message
            await self.send(json.dumps({
                'type': 'chat_message_chunk',
                'message': '',
                'is_complete': True
            }))
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    def _extract_tool_call(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract tool calls from message content"""
        pattern = r'<tool>(.*?)\((.*?)\)</tool>'
        match = re.search(pattern, content)
        
        if match:
            tool_name = match.group(1)
            args_str = match.group(2).strip('"\'')
            return {
                "name": tool_name,
                "arguments": {"query_description": args_str}
            }
        return None

    def test_db_connection(self):
        """Test database connection synchronously"""
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except OperationalError as e:
            logger.error(f"Database connection test failed: {str(e)}")
            raise
