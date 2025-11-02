import yaml
import os
from typing import List, Dict, Optional
from models.schemas import MCPServer


class MCPManager:
    """Manager for MCP (Model Context Protocol) servers"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv("MCP_CONFIG_PATH", "./config/mcp_servers.yaml")
        self.servers: Dict[str, MCPServer] = {}
        self.active_connections = {}
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
        """Initialize enabled MCP servers"""
        for name, server in self.servers.items():
            if server.enabled:
                try:
                    await self._connect_server(server)
                except Exception as e:
                    print(f"Error initializing MCP server {name}: {e}")

    async def _connect_server(self, server: MCPServer):
        """Connect to an MCP server (placeholder for actual implementation)"""
        # This will be implemented in Phase 2 with actual MCP SDK integration
        print(f"Connecting to MCP server: {server.name} (type: {server.type})")
        # TODO: Implement actual connection based on server type (stdio/http/websocket)

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
        # TODO: Disconnect server
        return True

    def get_available_tools(self) -> List[Dict]:
        """Get list of all available tools from enabled MCP servers"""
        # Placeholder - will be implemented with actual MCP integration
        return []
