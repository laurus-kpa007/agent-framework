import os
from typing import Optional
import httpx
from dotenv import load_dotenv
import asyncio

load_dotenv()


class OllamaService:
    """Service for managing Ollama connection and configuration

    Optimizations for TTFT:
    - Connection pooling with keep-alive
    - HTTP/2 support
    - Reduced timeouts for faster failures
    - Connection warmup
    """

    def __init__(self):
        self.endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/v1/")
        self.model = None  # No default model - user must select
        self.api_key = "ollama"  # Placeholder, Ollama doesn't require real API key

        # Connection pool with keep-alive for faster subsequent requests
        self._http_client = None
        self._connection_warmed_up = False
        self._model_loaded = False

    def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create a persistent HTTP client with connection pooling"""
        if self._http_client is None or self._http_client.is_closed:
            # Configure client for optimal performance
            limits = httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0,  # Keep connections alive for 30s
            )

            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=2.0,      # Fast connection timeout
                    read=60.0,        # Longer for streaming
                    write=5.0,
                    pool=2.0,
                ),
                limits=limits,
                http2=True,  # Enable HTTP/2 for multiplexing
                follow_redirects=True,
            )

        return self._http_client

    async def warmup_connection(self):
        """Warmup connection to Ollama for faster first request"""
        if self._connection_warmed_up:
            return

        try:
            base_url = self.endpoint.replace("/v1/", "").rstrip("/")
            client = self._get_http_client()
            # Make a quick request to establish connection
            await client.get(f"{base_url}/api/tags", timeout=2.0)
            self._connection_warmed_up = True
            print("✓ Ollama connection warmed up")
        except Exception as e:
            print(f"Connection warmup failed (non-critical): {e}")

    async def check_connection(self) -> bool:
        """Check if Ollama server is running and accessible"""
        try:
            base_url = self.endpoint.replace("/v1/", "").rstrip("/")
            client = self._get_http_client()
            response = await client.get(f"{base_url}/api/tags", timeout=3.0)
            return response.status_code == 200
        except Exception as e:
            print(f"Ollama connection error: {e}")
            return False

    async def list_models(self) -> list:
        """List available Ollama models with detailed information"""
        try:
            base_url = self.endpoint.replace("/v1/", "").rstrip("/")
            client = self._get_http_client()
            response = await client.get(f"{base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
        except Exception as e:
            print(f"Error listing models: {e}")
        return []

    async def load_model(self, model_name: str) -> bool:
        """Load a specific model into memory"""
        try:
            base_url = self.endpoint.replace("/v1/", "").rstrip("/")
            client = self._get_http_client()

            print(f"Loading model '{model_name}'...")

            # Send a minimal generation request to load model
            response = await client.post(
                f"{base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "Hi",
                    "stream": False,
                    "options": {
                        "num_predict": 1,  # Only generate 1 token
                    }
                },
                timeout=60.0  # Longer timeout for loading
            )
            if response.status_code == 200:
                self.model = model_name
                self._model_loaded = True
                print(f"✓ Model '{model_name}' loaded successfully")
                return True
            else:
                print(f"✗ Failed to load model '{model_name}': HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"Model load failed: {e}")
            return False

    def is_model_loaded(self) -> bool:
        """Check if a model is currently loaded"""
        return self._model_loaded and self.model is not None

    def get_current_model(self) -> Optional[str]:
        """Get currently loaded model name"""
        return self.model if self._model_loaded else None

    def get_config(self) -> dict:
        """Get Ollama configuration"""
        return {
            "endpoint": self.endpoint,
            "model": self.model,
            "api_key": self.api_key,
        }

    async def close(self):
        """Close the HTTP client connection pool"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
