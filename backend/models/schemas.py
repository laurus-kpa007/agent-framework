from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message")
    stream: bool = Field(default=True, description="Enable streaming response")


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="Agent response")
    tools_used: Optional[List[str]] = Field(default=None, description="List of tools used")


class MCPServerConfig(BaseModel):
    """MCP Server configuration"""
    command: str = Field(..., description="Command to run MCP server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")


class MCPServer(BaseModel):
    """MCP Server model"""
    name: str = Field(..., description="Server name")
    type: str = Field(..., description="Server type (stdio, http, websocket)")
    enabled: bool = Field(default=False, description="Is server enabled")
    description: Optional[str] = Field(default=None, description="Server description")
    config: MCPServerConfig = Field(..., description="Server configuration")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    ollama_connected: bool
    ollama_model: Optional[str] = None
    model_loaded: bool = False
    mcp_servers_count: int = 0
    active_tools_count: int = 0


class ModelInfo(BaseModel):
    """Ollama model information"""
    name: str = Field(..., description="Model name")
    size: Optional[int] = Field(default=None, description="Model size in bytes")
    modified_at: Optional[str] = Field(default=None, description="Last modified timestamp")
    digest: Optional[str] = Field(default=None, description="Model digest")


class ModelListResponse(BaseModel):
    """Model list response"""
    models: List[ModelInfo] = Field(default_factory=list, description="List of available models")
    current_model: Optional[str] = Field(default=None, description="Currently loaded model")
    model_loaded: bool = Field(default=False, description="Is a model currently loaded")


class ModelLoadRequest(BaseModel):
    """Model load request"""
    model_name: str = Field(..., description="Model name to load")


class ModelLoadResponse(BaseModel):
    """Model load response"""
    success: bool = Field(..., description="Load success status")
    model_name: str = Field(..., description="Loaded model name")
    message: str = Field(..., description="Status message")


class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")


class ConversationSession(BaseModel):
    """Conversation session model"""
    session_id: str = Field(..., description="Unique session ID")
    title: str = Field(..., description="Conversation title")
    messages: List[ChatMessage] = Field(default_factory=list, description="List of messages")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    model_name: Optional[str] = Field(default=None, description="Model used in this session")


class SessionListResponse(BaseModel):
    """Session list response"""
    sessions: List[ConversationSession] = Field(default_factory=list, description="List of sessions")


class SessionCreateRequest(BaseModel):
    """Session create request"""
    title: Optional[str] = Field(default="새로운 대화", description="Session title")


class SessionCreateResponse(BaseModel):
    """Session create response"""
    session_id: str = Field(..., description="Created session ID")
    title: str = Field(..., description="Session title")


class SessionDeleteResponse(BaseModel):
    """Session delete response"""
    success: bool = Field(..., description="Delete success status")
    message: str = Field(..., description="Status message")
