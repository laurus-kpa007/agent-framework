import os
from typing import Annotated, AsyncIterator, Optional, List
from random import randint
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv
import asyncio
from functools import lru_cache
from datetime import datetime

load_dotenv()


# Example tool functions
def get_weather(
    location: Annotated[str, "The location to get the weather for."],
) -> str:
    """Get the weather for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy", "partly cloudy"]
    temp = randint(10, 30)
    return f"The weather in {location} is {conditions[randint(0, len(conditions) - 1)]} with a high of {temp}°C."


def calculate(
    expression: Annotated[str, "Mathematical expression to evaluate (e.g., '2+2', '10*5')"],
) -> str:
    """Calculate a mathematical expression."""
    try:
        # Safe evaluation of simple math expressions
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"


# Optimized system prompt (shorter for faster processing)
SYSTEM_PROMPT = """You are a helpful AI assistant. Be concise and clear.
Available tools: weather lookup, calculator.
Use tools when needed and explain results briefly."""


class ChatAgentManager:
    """Manager for chat agent using Microsoft Agent Framework with Ollama

    Optimized for fast Time to First Token (TTFT):
    - Lazy initialization
    - Cached agent instances
    - Shorter system prompts
    - Parallel processing
    """

    def __init__(self, ollama_service, lazy_init: bool = True, mcp_manager=None):
        self.ollama_service = ollama_service
        self.mcp_manager = mcp_manager
        self.agent = None
        self.client = None
        self.tools_used = []
        self._init_lock = asyncio.Lock()
        self._initialized = False

        # Initialize immediately if not lazy
        if not lazy_init:
            self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the chat agent with Ollama configuration (synchronous)"""
        if self._initialized:
            return

        config = self.ollama_service.get_config()

        # Create OpenAI-compatible client pointing to Ollama (cached)
        self.client = OpenAIChatClient(
            api_key=config["api_key"],
            base_url=config["endpoint"],
            model_id=config["model"],
        )

        # Create agent WITHOUT tools to avoid compatibility issues
        # Models need to explicitly support function calling
        # Add current date/time to system prompt
        current_datetime = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
        current_day = datetime.now().strftime("%A")
        day_korean = {
            "Monday": "월요일",
            "Tuesday": "화요일",
            "Wednesday": "수요일",
            "Thursday": "목요일",
            "Friday": "금요일",
            "Saturday": "토요일",
            "Sunday": "일요일"
        }

        # Build tool descriptions for instructions
        tool_descriptions = []
        if self.mcp_manager:
            mcp_tools_info = self.mcp_manager.get_available_tools()
            for tool in mcp_tools_info[:20]:  # List first 20 tools
                tool_descriptions.append(f"- {tool['name']}: {tool['description'][:100]}")

        tool_list = "\n".join(tool_descriptions) if tool_descriptions else "없음"

        instructions = f"""당신은 유용한 AI 어시스턴트입니다. 항상 한국어로 답변하며, 간결하고 명확하게 응답하세요.

현재 시간 정보:
- 날짜 및 시간: {current_datetime}
- 요일: {day_korean.get(current_day, current_day)}

사용자가 "오늘", "지금", "현재" 등의 시간 관련 질문을 할 때 위 정보를 참고하세요.

사용 가능한 도구들:
{tool_list}

사용자의 요청을 해결하기 위해 필요하다면 위의 도구들을 적극적으로 활용하세요."""

        # Get MCP tools if available
        tools = []
        if self.mcp_manager:
            mcp_tools = self.mcp_manager.get_tool_functions()
            if mcp_tools:
                tools = mcp_tools
                print(f"✓ Loaded {len(tools)} MCP tools into agent")

        # Add example tools for testing
        tools.extend([get_weather, calculate])
        print(f"✓ Total tools loaded: {len(tools)}")

        # Create agent with tools
        if tools:
            self.agent = self.client.create_agent(
                name="OllamaAssistant",
                instructions=instructions,
                tools=tools
            )
        else:
            self.agent = self.client.create_agent(
                name="OllamaAssistant",
                instructions=instructions,
            )

        self._initialized = True

    async def _ensure_initialized(self):
        """Ensure agent is initialized (async lazy loading)"""
        if self._initialized:
            return

        async with self._init_lock:
            if not self._initialized:
                # Run synchronous initialization in executor to avoid blocking
                await asyncio.get_event_loop().run_in_executor(
                    None, self._initialize_agent
                )

    async def chat(self, message: str) -> str:
        """Send a message and get a response (non-streaming)"""
        await self._ensure_initialized()
        self.tools_used = []
        result = await self.agent.run(message)
        # Extract text from AgentRunResponse
        if hasattr(result, 'text'):
            return result.text
        return str(result)

    async def chat_stream(self, message: str) -> AsyncIterator[str]:
        """Send a message and stream the response (optimized for TTFT)"""
        # Ensure agent is initialized while preparing the request
        await self._ensure_initialized()
        self.tools_used = []

        # Start streaming immediately to reduce TTFT
        first_chunk = True
        async for chunk in self.agent.run_stream(message):
            if chunk.text:
                if first_chunk:
                    # Log TTFT optimization
                    first_chunk = False
                yield chunk.text

    async def warmup(self):
        """Warmup the agent with a simple query to reduce cold start"""
        await self._ensure_initialized()
        try:
            # Send a minimal query to warm up the model
            async for _ in self.agent.run_stream("Hi"):
                break  # Just get first token
        except Exception as e:
            print(f"Warmup failed: {e}")

    async def reload_with_model(self, model_name: str):
        """Reload agent with a different model"""
        try:
            # Update ollama service model
            self.ollama_service.model = model_name
            self.ollama_service._model_loaded = True

            # Reset initialization
            self._initialized = False
            self.agent = None
            self.client = None

            # Reinitialize with new model
            await self._ensure_initialized()

            # Warmup new model
            await self.warmup()

            print(f"✓ Agent reloaded with model '{model_name}'")
            return True
        except Exception as e:
            print(f"Failed to reload agent with model '{model_name}': {e}")
            return False

    def add_tool(self, tool_function):
        """Add a new tool to the agent (for MCP integration later)"""
        # This will be enhanced when we add MCP support
        pass

    def get_active_tools(self) -> List[str]:
        """Get list of currently active tools"""
        # Return list of actual tool names that were used in the last response
        # For now, return all available tool names from MCP
        if self.mcp_manager:
            all_tools = self.mcp_manager.get_available_tools()
            return [tool["name"] for tool in all_tools[:10]]  # Limit to first 10 for display
        return []

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized"""
        return self._initialized
