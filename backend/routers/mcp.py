from fastapi import APIRouter, HTTPException
from typing import List
import yaml
import os

from models.schemas import MCPServer

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


def load_mcp_servers() -> List[MCPServer]:
    """Load MCP servers from configuration file"""
    config_path = os.getenv("MCP_CONFIG_PATH", "./config/mcp_servers.yaml")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            servers = config.get("mcp_servers", [])
            return [MCPServer(**server) for server in servers]
    except FileNotFoundError:
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading MCP config: {str(e)}")


@router.get("/servers", response_model=List[MCPServer])
async def get_mcp_servers():
    """Get list of configured MCP servers"""
    return load_mcp_servers()


@router.get("/tools")
async def get_mcp_tools():
    """Get list of all available MCP tools"""
    # Placeholder for MCP tools discovery
    # Will be implemented when MCP integration is complete
    return {
        "tools": [],
        "message": "MCP tools discovery not yet implemented"
    }


@router.post("/servers/{server_name}/toggle")
async def toggle_mcp_server(server_name: str):
    """Enable or disable an MCP server"""
    # Placeholder for dynamic server management
    # Will be implemented in Phase 2
    return {
        "message": f"Server {server_name} toggle not yet implemented",
        "status": "pending"
    }


@router.post("/test/{server_name}")
async def test_mcp_server(server_name: str):
    """Test MCP server connection"""
    # Placeholder for server testing
    return {
        "server": server_name,
        "status": "test_not_implemented",
        "message": "MCP server testing will be implemented in Phase 2"
    }
