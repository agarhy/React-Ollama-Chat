"""
Database interface for conversation storage.
Supports multiple backends: SQLite, MySQL, JSON, CSV
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class Message(BaseModel):
    id: Optional[int] = None
    conversation_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    model: Optional[str] = None


class Conversation(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model: Optional[str] = None


class DatabaseInterface(ABC):
    """Abstract interface for conversation storage"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the database/storage"""
        pass
    
    @abstractmethod
    async def create_conversation(self, conversation_id: str, title: str = None, model: str = None) -> Conversation:
        """Create a new conversation"""
        pass
    
    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        pass
    
    @abstractmethod
    async def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """List all conversations"""
        pass
    
    @abstractmethod
    async def add_message(self, message: Message) -> Message:
        """Add a message to a conversation"""
        pass
    
    @abstractmethod
    async def get_messages(self, conversation_id: str) -> List[Message]:
        """Get all messages for a conversation"""
        pass
    
    @abstractmethod
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear all messages in a conversation"""
        pass
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close database connection"""
        pass
