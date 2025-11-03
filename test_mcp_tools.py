#!/usr/bin/env python3
"""Quick test script to verify MCP tools loading"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from mcp_integration import MCPManager


async def test_mcp_manager():
    print("=" * 60)
    print("Testing MCP Manager")
    print("=" * 60)

    # Initialize MCP Manager
    print("\n1. Creating MCP Manager...")
    manager = MCPManager()

    # Check loaded servers
    servers = manager.get_servers()
    print(f"   Loaded {len(servers)} servers from config")
    for server in servers:
        print(f"   - {server.name}: enabled={server.enabled}")

    # Initialize servers
    print("\n2. Initializing MCP servers...")
    await manager.initialize_servers()

    # Check enabled servers
    enabled = manager.get_enabled_servers()
    print(f"   ✓ {len(enabled)} servers enabled")

    # Get available tools
    print("\n3. Getting available tools...")
    tools = manager.get_available_tools()
    print(f"   ✓ Found {len(tools)} tools:")
    for tool in tools[:10]:  # Show first 10
        print(f"   - {tool['name']} (from {tool['server']})")
    if len(tools) > 10:
        print(f"   ... and {len(tools) - 10} more")

    print("\n" + "=" * 60)
    print(f"RESULT: {'✓ PASS' if len(tools) > 0 else '✗ FAIL'}")
    print(f"Tools count: {len(tools)}")
    print("=" * 60)

    # Cleanup
    await manager.cleanup()

    return len(tools)


if __name__ == "__main__":
    try:
        tools_count = asyncio.run(test_mcp_manager())
        sys.exit(0 if tools_count > 0 else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
