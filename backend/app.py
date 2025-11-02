from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend directory to Python path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from routers import chat_router, mcp_router
from routers.chat import ollama_service, chat_agent
from services import OllamaService
from agents import ChatAgentManager
from mcp_integration import MCPManager

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Ollama Agent Framework Chat",
    description="Web UI for chatting with Ollama using Microsoft Agent Framework and MCP",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services with optimizations
_ollama_service = OllamaService()
_mcp_manager = MCPManager()
_chat_agent = ChatAgentManager(_ollama_service, lazy_init=True, mcp_manager=_mcp_manager)  # Lazy init for faster startup

# Set global instances in routers
import routers.chat as chat_module
chat_module.ollama_service = _ollama_service
chat_module.chat_agent = _chat_agent

# Include routers
app.include_router(chat_router)
app.include_router(mcp_router)

# Templates
templates = Jinja2Templates(directory="../frontend/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("\n" + "="*60)
    print("🚀 Starting Ollama Agent Framework Chat")
    print("="*60)
    print(f"Ollama Endpoint: {_ollama_service.endpoint}")
    print()

    # Check Ollama connection
    print("Checking Ollama connection...")
    if await _ollama_service.check_connection():
        print("✓ Ollama connection successful")

        # Warmup connection pool only
        print("Warming up connection pool...")
        await _ollama_service.warmup_connection()

        # List available models
        models = await _ollama_service.list_models()
        print(f"✓ Found {len(models)} available models")
        if models:
            print("  Available models:")
            for model in models[:5]:  # Show first 5
                print(f"    - {model.get('name', 'unknown')}")
            if len(models) > 5:
                print(f"    ... and {len(models) - 5} more")

        print("\n⚠️  No model loaded. Please select a model from the Web UI.")
    else:
        print("✗ Warning: Cannot connect to Ollama. Please ensure Ollama is running.")

    # Initialize MCP servers
    print("\nInitializing MCP servers...")
    await _mcp_manager.initialize_servers()
    enabled_servers = _mcp_manager.get_enabled_servers()
    print(f"✓ MCP servers loaded: {len(enabled_servers)} enabled")

    print("\n" + "="*60)
    print("✓ Server ready!")
    print("  Open http://localhost:8000 and select a model to start")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    print("\nShutting down...")
    await _mcp_manager.cleanup()
    await _ollama_service.close()
    print("✓ Cleanup complete")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main chat UI"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Ollama Agent Chat"
    })


@app.get("/mcp-settings", response_class=HTMLResponse)
async def mcp_settings(request: Request):
    """Serve the MCP settings UI"""
    return templates.TemplateResponse("mcp-settings.html", {
        "request": request,
        "title": "MCP Settings"
    })


@app.get("/api/info")
async def get_info():
    """Get application information"""
    return {
        "name": "Ollama Agent Framework Chat",
        "version": "1.0.0",
        "ollama_endpoint": _ollama_service.endpoint,
        "ollama_model": _ollama_service.model,
        "mcp_servers_count": len(_mcp_manager.get_servers()),
        "mcp_enabled_count": len(_mcp_manager.get_enabled_servers()),
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    print(f"\n{'='*60}")
    print(f"🚀 Starting server on http://{host}:{port}")
    print(f"{'='*60}\n")

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
