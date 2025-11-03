from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import AsyncIterator
import json

from models.schemas import (
    ChatRequest, ChatResponse, HealthResponse,
    ModelListResponse, ModelInfo, ModelLoadRequest, ModelLoadResponse
)
from services import OllamaService
from agents import ChatAgentManager
from mcp_integration import MCPManager

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Global instances (will be initialized in main app)
ollama_service: OllamaService = None
chat_agent: ChatAgentManager = None
mcp_manager: MCPManager = None


def get_chat_agent() -> ChatAgentManager:
    """Dependency to get chat agent instance"""
    if chat_agent is None:
        raise HTTPException(status_code=503, detail="Chat agent not initialized")
    return chat_agent


def get_ollama_service() -> OllamaService:
    """Dependency to get ollama service instance"""
    if ollama_service is None:
        raise HTTPException(status_code=503, detail="Ollama service not initialized")
    return ollama_service


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    agent: ChatAgentManager = Depends(get_chat_agent)
):
    """Send a message and get a complete response (non-streaming)"""
    try:
        response = await agent.chat(request.message)
        return ChatResponse(
            response=response,
            tools_used=agent.get_active_tools()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.post("/stream")
async def stream_message(
    request: ChatRequest,
    agent: ChatAgentManager = Depends(get_chat_agent)
):
    """Send a message and stream the response using Server-Sent Events

    Optimized for TTFT:
    - Immediate response headers
    - No buffering
    - Minimal JSON overhead
    - Fast event formatting
    """

    async def event_generator() -> AsyncIterator[str]:
        try:
            # Send an immediate "thinking" event to show responsiveness
            yield f"data: {json.dumps({'status': 'processing', 'done': False})}\n\n"

            # Stream the response with minimal latency
            chunk_count = 0
            async for chunk in agent.chat_stream(request.message):
                # Format as SSE with minimal overhead
                data = json.dumps({"text": chunk, "done": False}, separators=(',', ':'))
                yield f"data: {data}\n\n"
                chunk_count += 1

            # Send completion event
            final_data = json.dumps({
                "text": "",
                "done": True,
                "tools_used": agent.get_active_tools(),
                "chunks": chunk_count
            }, separators=(',', ':'))
            yield f"data: {final_data}\n\n"

        except Exception as e:
            error_data = json.dumps({"error": str(e), "done": True}, separators=(',', ':'))
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
            "Content-Type": "text/event-stream; charset=utf-8",
            "Transfer-Encoding": "chunked",
        }
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(
    service: OllamaService = Depends(get_ollama_service),
    agent: ChatAgentManager = Depends(get_chat_agent)
):
    """Check health status of Ollama and agent"""
    ollama_connected = await service.check_connection()

    # Get MCP tools count directly from MCP Manager
    mcp_tools_count = 0
    mcp_servers_enabled = 0
    if mcp_manager:
        mcp_tools_count = len(mcp_manager.get_available_tools())
        mcp_servers_enabled = len(mcp_manager.get_enabled_servers())

    return HealthResponse(
        status="healthy" if ollama_connected else "degraded",
        ollama_connected=ollama_connected,
        ollama_model=service.get_current_model(),
        model_loaded=service.is_model_loaded(),
        mcp_servers_count=mcp_servers_enabled,
        active_tools_count=mcp_tools_count
    )


@router.get("/models", response_model=ModelListResponse)
async def list_models(service: OllamaService = Depends(get_ollama_service)):
    """List available Ollama models"""
    models_data = await service.list_models()

    models = [
        ModelInfo(
            name=model.get("name", ""),
            size=model.get("size"),
            modified_at=model.get("modified_at"),
            digest=model.get("digest")
        )
        for model in models_data
    ]

    return ModelListResponse(
        models=models,
        current_model=service.get_current_model(),
        model_loaded=service.is_model_loaded()
    )


@router.post("/models/load", response_model=ModelLoadResponse)
async def load_model(
    request: ModelLoadRequest,
    service: OllamaService = Depends(get_ollama_service),
    agent: ChatAgentManager = Depends(get_chat_agent)
):
    """Load a specific model and reinitialize agent"""
    try:
        # Load model in Ollama
        success = await service.load_model(request.model_name)

        if not success:
            return ModelLoadResponse(
                success=False,
                model_name=request.model_name,
                message=f"Failed to load model '{request.model_name}'"
            )

        # Reload agent with new model
        agent_success = await agent.reload_with_model(request.model_name)

        if not agent_success:
            return ModelLoadResponse(
                success=False,
                model_name=request.model_name,
                message=f"Model loaded but agent initialization failed"
            )

        return ModelLoadResponse(
            success=True,
            model_name=request.model_name,
            message=f"Model '{request.model_name}' loaded successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model: {str(e)}")
