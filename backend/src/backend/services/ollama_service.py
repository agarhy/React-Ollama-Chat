"""
Ollama service for interacting with the local Ollama API
"""
import ollama
import os
from typing import List, Dict, Any, AsyncGenerator
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from ddgs import DDGS


class OllamaService:
    """Service for interacting with Ollama API"""

    def __init__(self):
        # Get Ollama configuration from environment variables
        ollama_host = os.getenv('OLLAMA_HOST', 'localhost')
        ollama_port = os.getenv('OLLAMA_PORT', '11434')
        ollama_base_url = os.getenv('OLLAMA_BASE_URL', f'http://{ollama_host}:{ollama_port}')

        self.client = ollama.Client(host=ollama_base_url)
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from Ollama"""
        try:
            loop = asyncio.get_event_loop()
            models = await loop.run_in_executor(
                self.executor,
                self.client.list
            )
            return models.get('models', [])
        except Exception as e:
            print(f"Error getting models: {e}")
            return []
    
    async def chat(self, model: str, messages: List[Dict[str, str]], stream: bool = False) -> Dict[str, Any]:
        """Send chat request to Ollama
        
        Args:
            model: Model name to use
            messages: List of messages in OpenAI format
            stream: Whether to stream the response
            
        Returns:
            Response from Ollama
        """
        try:
            loop = asyncio.get_event_loop()
            
            if stream:
                # For streaming, we'll return the generator
                return await self._chat_stream(model, messages)
            else:
                # For non-streaming, run in executor
                response = await loop.run_in_executor(
                    self.executor,
                    lambda: self.client.chat(model=model, messages=messages)
                )
                return response
        except Exception as e:
            print(f"Error in chat: {e}")
            raise e
    
    async def _chat_stream(self, model: str, messages: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response from Ollama"""
        try:
            loop = asyncio.get_event_loop()
            
            # Run the streaming chat in executor
            def _stream_chat():
                return self.client.chat(model=model, messages=messages, stream=True)
            
            stream = await loop.run_in_executor(self.executor, _stream_chat)
            
            for chunk in stream:
                yield chunk
                
        except Exception as e:
            print(f"Error in streaming chat: {e}")
            raise e
    
    async def generate(self, model: str, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """Generate response using Ollama
        
        Args:
            model: Model name to use
            prompt: Input prompt
            stream: Whether to stream the response
            
        Returns:
            Response from Ollama
        """
        try:
            loop = asyncio.get_event_loop()
            
            if stream:
                return await self._generate_stream(model, prompt)
            else:
                response = await loop.run_in_executor(
                    self.executor,
                    lambda: self.client.generate(model=model, prompt=prompt)
                )
                return response
        except Exception as e:
            print(f"Error in generate: {e}")
            raise e
    
    async def _generate_stream(self, model: str, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream generate response from Ollama"""
        try:
            loop = asyncio.get_event_loop()
            
            def _stream_generate():
                return self.client.generate(model=model, prompt=prompt, stream=True)
            
            stream = await loop.run_in_executor(self.executor, _stream_generate)
            
            for chunk in stream:
                yield chunk
                
        except Exception as e:
            print(f"Error in streaming generate: {e}")
            raise e
    
    async def pull_model(self, model: str) -> Dict[str, Any]:
        """Pull a model from Ollama registry
        
        Args:
            model: Model name to pull
            
        Returns:
            Response from Ollama
        """
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                lambda: self.client.pull(model)
            )
            return response
        except Exception as e:
            print(f"Error pulling model: {e}")
            raise e
    
    async def check_model_exists(self, model: str) -> bool:
        """Check if a model exists locally
        
        Args:
            model: Model name to check
            
        Returns:
            True if model exists, False otherwise
        """
        try:
            models = await self.get_available_models()
            model_names = [m.get('name', '') for m in models]
            return model in model_names
        except Exception:
            return False
    
    async def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web using DuckDuckGo"""
        try:
            loop = asyncio.get_event_loop()

            def _search():
                with DDGS() as ddgs:
                    results = []
                    for result in ddgs.text(query, max_results=max_results):
                        results.append({
                            'title': result.get('title', ''),
                            'body': result.get('body', ''),
                            'href': result.get('href', ''),
                        })
                    return results

            return await loop.run_in_executor(self.executor, _search)
        except Exception as e:
            print(f"Error in web search: {e}")
            return []

    def get_current_datetime(self) -> Dict[str, Any]:
        """Get current date and time information"""
        now = datetime.now()
        return {
            'datetime': now.isoformat(),
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'day_of_week': now.strftime('%A'),
            'month': now.strftime('%B'),
            'year': now.year,
            'timestamp': now.timestamp()
        }

    async def enhanced_chat(self, model: str, messages: List[Dict[str, str]],
                          enable_search: bool = False, stream: bool = False) -> Dict[str, Any]:
        """Enhanced chat with search and datetime capabilities"""
        try:
            # Add system context with current datetime
            datetime_info = self.get_current_datetime()
            system_message = {
                "role": "system",
                "content": f"Current date and time: {datetime_info['datetime']} ({datetime_info['day_of_week']}, {datetime_info['month']} {datetime_info['date']}, {datetime_info['year']})"
            }

            # Check if user is asking for search
            user_message = messages[-1]['content'].lower() if messages else ""
            search_keywords = ['search', 'find', 'look up', 'what is', 'who is', 'when did', 'latest news']
            needs_search = enable_search and any(keyword in user_message for keyword in search_keywords)

            enhanced_messages = [system_message] + messages

            if needs_search:
                # Extract search query from user message
                search_query = messages[-1]['content']
                search_results = await self.search_web(search_query, max_results=3)

                if search_results:
                    search_context = "Here are some recent search results:\n"
                    for i, result in enumerate(search_results, 1):
                        search_context += f"{i}. {result['title']}: {result['body'][:200]}...\n"

                    search_message = {
                        "role": "system",
                        "content": search_context
                    }
                    enhanced_messages.append(search_message)

            return await self.chat(model, enhanced_messages, stream)

        except Exception as e:
            print(f"Error in enhanced chat: {e}")
            return await self.chat(model, messages, stream)

    def close(self):
        """Close the service and cleanup resources"""
        self.executor.shutdown(wait=True)
