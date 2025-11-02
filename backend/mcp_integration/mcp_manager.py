import yaml
import os
import asyncio
from typing import List, Dict, Optional, Any, Callable
from models.schemas import MCPServer
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack


class MCPManager:
    """Manager for MCP (Model Context Protocol) servers with actual tool integration"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv("MCP_CONFIG_PATH", "./config/mcp_servers.yaml")
        self.servers: Dict[str, MCPServer] = {}
        self.active_connections: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.tools_cache: Dict[str, List[Any]] = {}
        self._load_servers()

    def _load_servers(self):
        """Load MCP servers from configuration file"""
        try:
            if not os.path.exists(self.config_path):
                print(f"MCP config file not found: {self.config_path}")
                return

            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                servers_config = config.get("mcp_servers", [])

                for server_data in servers_config:
                    try:
                        server = MCPServer(**server_data)
                        self.servers[server.name] = server
                        print(f"Loaded MCP server: {server.name} (enabled: {server.enabled})")
                    except Exception as e:
                        print(f"Error loading MCP server {server_data.get('name', 'unknown')}: {e}")

        except Exception as e:
            print(f"Error loading MCP configuration: {e}")

    async def initialize_servers(self):
        """Initialize enabled MCP servers and establish connections"""
        for name, server in self.servers.items():
            if server.enabled:
                try:
                    await self._connect_server(server)
                except Exception as e:
                    print(f"Error initializing MCP server {name}: {e}")

    async def _connect_server(self, server: MCPServer):
        """Connect to an MCP server and cache its tools"""
        try:
            print(f"Connecting to MCP server: {server.name} (type: {server.type})")

            if server.type == "stdio":
                # Prepare environment variables
                env = dict(os.environ)
                if server.env:
                    for key, value in server.env.items():
                        # Expand environment variables in values
                        if value.startswith("${") and value.endswith("}"):
                            env_var = value[2:-1]
                            value = os.getenv(env_var, "")
                        env[key] = value

                # Create server parameters
                server_params = StdioServerParameters(
                    command=server.config.command,
                    args=server.config.args,
                    env=env
                )

                # Establish connection
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                read, write = stdio_transport

                session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )

                # Initialize session
                await session.initialize()

                # Store connection
                self.active_connections[server.name] = session

                # List and cache tools
                tools_result = await session.list_tools()
                self.tools_cache[server.name] = tools_result.tools

                print(f"✓ Connected to {server.name}, found {len(tools_result.tools)} tools:")
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")

            else:
                print(f"⚠ Server type '{server.type}' not yet implemented for {server.name}")

        except Exception as e:
            print(f"✗ Failed to connect to {server.name}: {e}")
            import traceback
            traceback.print_exc()

    def get_servers(self) -> List[MCPServer]:
        """Get list of all configured servers"""
        return list(self.servers.values())

    def get_enabled_servers(self) -> List[MCPServer]:
        """Get list of enabled servers"""
        return [s for s in self.servers.values() if s.enabled]

    def get_server(self, name: str) -> Optional[MCPServer]:
        """Get a specific server by name"""
        return self.servers.get(name)

    async def enable_server(self, name: str) -> bool:
        """Enable a server"""
        server = self.servers.get(name)
        if not server:
            return False

        server.enabled = True
        await self._connect_server(server)
        return True

    async def disable_server(self, name: str) -> bool:
        """Disable a server"""
        server = self.servers.get(name)
        if not server:
            return False

        server.enabled = False

        # Disconnect server
        if name in self.active_connections:
            del self.active_connections[name]
        if name in self.tools_cache:
            del self.tools_cache[name]

        return True

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available tools from enabled MCP servers"""
        all_tools = []
        for server_name, tools in self.tools_cache.items():
            for tool in tools:
                all_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "server": server_name,
                    "schema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                })
        return all_tools

    def get_tool_functions(self) -> List[Callable]:
        """Get callable tool functions for Agent Framework integration"""
        tool_functions = []

        for server_name, session in self.active_connections.items():
            tools = self.tools_cache.get(server_name, [])

            for tool in tools:
                # Create a wrapper function for each MCP tool
                async def tool_wrapper(session=session, tool_name=tool.name, **kwargs):
                    """Dynamically created MCP tool wrapper"""
                    try:
                        result = await session.call_tool(tool_name, arguments=kwargs)
                        # Extract content from result
                        if hasattr(result, 'content') and result.content:
                            return str(result.content[0].text if hasattr(result.content[0], 'text') else result.content[0])
                        return str(result)
                    except Exception as e:
                        return f"Error calling tool {tool_name}: {str(e)}"

                # Set function metadata for Agent Framework
                tool_wrapper.__name__ = tool.name
                tool_wrapper.__doc__ = tool.description

                # Add annotations if input schema is available
                if hasattr(tool, 'inputSchema') and 'properties' in tool.inputSchema:
                    annotations = {}
                    for param_name, param_info in tool.inputSchema['properties'].items():
                        param_desc = param_info.get('description', '')
                        annotations[param_name] = str  # Default to string type
                    tool_wrapper.__annotations__ = annotations

                tool_functions.append(tool_wrapper)

        return tool_functions

    async def cleanup(self):
        """Cleanup all connections"""
        await self.exit_stack.aclose()
        self.active_connections.clear()
        self.tools_cache.clear()
