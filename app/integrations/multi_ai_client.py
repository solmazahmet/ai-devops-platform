"""
Multi-Model AI Client
Support for multiple AI models: OpenAI, Claude, Gemini, etc.
"""

import asyncio
import aiohttp
import json
import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from abc import ABC, abstractmethod

from app.core.config import settings

logger = logging.getLogger(__name__)

class AIModel(str, Enum):
    """Supported AI models"""
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229" 
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    GEMINI_PRO = "gemini-pro"
    GEMINI_1_5_PRO = "gemini-1.5-pro"

class AIProvider(str, Enum):
    """AI providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    GOOGLE = "google"

class AIResponse:
    """Standardized AI response"""
    def __init__(self, content: str, model: str, provider: str, tokens_used: int = 0, 
                 cost: float = 0.0, confidence: float = 1.0, metadata: Dict[str, Any] = None):
        self.content = content
        self.model = model
        self.provider = provider
        self.tokens_used = tokens_used
        self.cost = cost
        self.confidence = confidence
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

class BaseAIClient(ABC):
    """Base class for AI clients"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.base_url = ""
        self.headers = {}
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> AIResponse:
        """Generate response from AI model"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check if the AI service is available"""
        pass
    
    def _calculate_cost(self, tokens: int, model: str) -> float:
        """Calculate approximate cost based on tokens and model"""
        # Pricing per 1K tokens (approximate, as of 2024)
        pricing = {
            "gpt-3.5-turbo": 0.0015,
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "claude-3-haiku": 0.00025,
            "claude-3-sonnet": 0.003,
            "claude-3-opus": 0.015,
            "gemini-pro": 0.0005,
            "gemini-1.5-pro": 0.007
        }
        
        rate = pricing.get(model, 0.001)
        return (tokens / 1000) * rate

class OpenAIClient(BaseAIClient):
    """OpenAI API client"""
    
    def __init__(self, api_key: str, model: str = AIModel.GPT_3_5_TURBO):
        super().__init__(api_key, model)
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_response(self, prompt: str, **kwargs) -> AIResponse:
        """Generate response using OpenAI API"""
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": kwargs.get("max_tokens", 2000),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 1.0)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        tokens_used = data["usage"]["total_tokens"]
                        cost = self._calculate_cost(tokens_used, self.model)
                        
                        return AIResponse(
                            content=content,
                            model=self.model,
                            provider=AIProvider.OPENAI,
                            tokens_used=tokens_used,
                            cost=cost,
                            metadata={"finish_reason": data["choices"][0]["finish_reason"]}
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(f"OpenAI API error {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "provider": AIProvider.OPENAI,
                            "model": self.model,
                            "available": True
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "provider": AIProvider.OPENAI,
                            "error": f"HTTP {response.status}",
                            "available": False
                        }
                        
        except Exception as e:
            return {
                "status": "error",
                "provider": AIProvider.OPENAI,
                "error": str(e),
                "available": False
            }

class AnthropicClient(BaseAIClient):
    """Anthropic Claude API client"""
    
    def __init__(self, api_key: str, model: str = AIModel.CLAUDE_3_SONNET):
        super().__init__(api_key, model)
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    async def generate_response(self, prompt: str, **kwargs) -> AIResponse:
        """Generate response using Anthropic Claude API"""
        try:
            payload = {
                "model": self.model,
                "max_tokens": kwargs.get("max_tokens", 2000),
                "temperature": kwargs.get("temperature", 0.7),
                "messages": [{"role": "user", "content": prompt}]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data["content"][0]["text"]
                        tokens_used = data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
                        cost = self._calculate_cost(tokens_used, self.model)
                        
                        return AIResponse(
                            content=content,
                            model=self.model,
                            provider=AIProvider.ANTHROPIC,
                            tokens_used=tokens_used,
                            cost=cost,
                            metadata={"stop_reason": data.get("stop_reason")}
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(f"Anthropic API error {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Anthropic API health"""
        try:
            # Simple test message
            test_payload = {
                "model": self.model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hello"}]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=test_payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "provider": AIProvider.ANTHROPIC,
                            "model": self.model,
                            "available": True
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "provider": AIProvider.ANTHROPIC,
                            "error": f"HTTP {response.status}",
                            "available": False
                        }
                        
        except Exception as e:
            return {
                "status": "error",
                "provider": AIProvider.ANTHROPIC,
                "error": str(e),
                "available": False
            }

class GoogleClient(BaseAIClient):
    """Google Gemini API client"""
    
    def __init__(self, api_key: str, model: str = AIModel.GEMINI_PRO):
        super().__init__(api_key, model)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.headers = {
            "Content-Type": "application/json"
        }
    
    async def generate_response(self, prompt: str, **kwargs) -> AIResponse:
        """Generate response using Google Gemini API"""
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "topP": kwargs.get("top_p", 1.0),
                    "maxOutputTokens": kwargs.get("max_tokens", 2000)
                }
            }
            
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data["candidates"][0]["content"]["parts"][0]["text"]
                        
                        # Google doesn't provide token usage in the same way
                        estimated_tokens = len(content.split()) * 1.3  # Rough estimation
                        cost = self._calculate_cost(int(estimated_tokens), self.model)
                        
                        return AIResponse(
                            content=content,
                            model=self.model,
                            provider=AIProvider.GOOGLE,
                            tokens_used=int(estimated_tokens),
                            cost=cost,
                            metadata={"finish_reason": data["candidates"][0].get("finishReason")}
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(f"Google API error {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"Google generation error: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Google Gemini API health"""
        try:
            # Simple test message
            test_payload = {
                "contents": [{"parts": [{"text": "Hello"}]}],
                "generationConfig": {"maxOutputTokens": 10}
            }
            
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=test_payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "provider": AIProvider.GOOGLE,
                            "model": self.model,
                            "available": True
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "provider": AIProvider.GOOGLE,
                            "error": f"HTTP {response.status}",
                            "available": False
                        }
                        
        except Exception as e:
            return {
                "status": "error",
                "provider": AIProvider.GOOGLE,
                "error": str(e),
                "available": False
            }

class MultiAIManager:
    """Manager for multiple AI clients"""
    
    def __init__(self):
        self.clients: Dict[str, BaseAIClient] = {}
        self.fallback_order: List[str] = []
        self.load_balancing = False
        self.current_client_index = 0
        
        # Initialize clients based on available API keys
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI clients based on available configuration"""
        
        # OpenAI
        if settings.OPENAI_API_KEY:
            self.clients["openai_gpt35"] = OpenAIClient(
                settings.OPENAI_API_KEY, 
                AIModel.GPT_3_5_TURBO
            )
            self.clients["openai_gpt4"] = OpenAIClient(
                settings.OPENAI_API_KEY, 
                AIModel.GPT_4
            )
            self.fallback_order.extend(["openai_gpt35", "openai_gpt4"])
        
        # Anthropic Claude (if API key is available)
        anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if anthropic_key:
            self.clients["claude_sonnet"] = AnthropicClient(
                anthropic_key, 
                AIModel.CLAUDE_3_SONNET
            )
            self.clients["claude_haiku"] = AnthropicClient(
                anthropic_key, 
                AIModel.CLAUDE_3_HAIKU
            )
            self.fallback_order.extend(["claude_sonnet", "claude_haiku"])
        
        # Google Gemini (if API key is available)
        google_key = getattr(settings, 'GOOGLE_API_KEY', None)
        if google_key:
            self.clients["gemini_pro"] = GoogleClient(
                google_key, 
                AIModel.GEMINI_PRO
            )
            self.fallback_order.append("gemini_pro")
        
        logger.info(f"Initialized AI clients: {list(self.clients.keys())}")
    
    async def generate_response(self, prompt: str, model: Optional[str] = None, 
                              use_fallback: bool = True, **kwargs) -> AIResponse:
        """Generate response using specified model or fallback chain"""
        
        if model and model in self.clients:
            # Use specific model
            try:
                return await self.clients[model].generate_response(prompt, **kwargs)
            except Exception as e:
                logger.error(f"Error with model {model}: {e}")
                if not use_fallback:
                    raise
        
        # Use fallback chain or load balancing
        if self.load_balancing:
            return await self._load_balanced_generation(prompt, **kwargs)
        else:
            return await self._fallback_generation(prompt, **kwargs)
    
    async def _fallback_generation(self, prompt: str, **kwargs) -> AIResponse:
        """Try models in fallback order"""
        last_error = None
        
        for client_name in self.fallback_order:
            if client_name not in self.clients:
                continue
                
            try:
                logger.info(f"Trying AI model: {client_name}")
                response = await self.clients[client_name].generate_response(prompt, **kwargs)
                logger.info(f"Successfully used model: {client_name}")
                return response
                
            except Exception as e:
                logger.warning(f"Model {client_name} failed: {e}")
                last_error = e
                continue
        
        # If all models failed
        if last_error:
            raise Exception(f"All AI models failed. Last error: {last_error}")
        else:
            raise Exception("No AI models available")
    
    async def _load_balanced_generation(self, prompt: str, **kwargs) -> AIResponse:
        """Distribute requests across available models"""
        if not self.fallback_order:
            raise Exception("No AI models available")
        
        # Round-robin selection
        client_name = self.fallback_order[self.current_client_index]
        self.current_client_index = (self.current_client_index + 1) % len(self.fallback_order)
        
        try:
            return await self.clients[client_name].generate_response(prompt, **kwargs)
        except Exception as e:
            logger.warning(f"Load balanced model {client_name} failed: {e}")
            # Fall back to fallback chain
            return await self._fallback_generation(prompt, **kwargs)
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all AI clients"""
        health_results = {}
        
        for client_name, client in self.clients.items():
            try:
                health_results[client_name] = await client.health_check()
            except Exception as e:
                health_results[client_name] = {
                    "status": "error",
                    "error": str(e),
                    "available": False
                }
        
        return health_results
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        models = []
        
        for client_name, client in self.clients.items():
            models.append({
                "name": client_name,
                "model": client.model,
                "provider": getattr(client, 'provider', 'unknown'),
                "available": True
            })
        
        return models
    
    def enable_load_balancing(self, enabled: bool = True):
        """Enable or disable load balancing"""
        self.load_balancing = enabled
        logger.info(f"Load balancing {'enabled' if enabled else 'disabled'}")
    
    def set_fallback_order(self, order: List[str]):
        """Set custom fallback order"""
        # Validate that all models in order exist
        valid_order = [model for model in order if model in self.clients]
        self.fallback_order = valid_order
        logger.info(f"Fallback order set to: {valid_order}")

# Global multi-AI manager instance
multi_ai_manager = MultiAIManager()