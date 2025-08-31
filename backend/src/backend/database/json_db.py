"""
JSON file implementation of the database interface
"""
import json
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from .interface import DatabaseInterface, Message, Conversation


class JSONDatabase(DatabaseInterface):
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.conversations_file = self.data_dir / "conversations.json"
        self.messages_file = self.data_dir / "messages.json"
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize JSON files"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.conversations_file.exists():
            await self._write_json(self.conversations_file, {})
        
        if not self.messages_file.exists():
            await self._write_json(self.messages_file, {})
    
    async def _read_json(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON file safely"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    async def _write_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write JSON file safely"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    async def create_conversation(self, conversation_id: str, title: str = None, model: str = None) -> Conversation:
        """Create a new conversation"""
        async with self._lock:
            conversations = await self._read_json(self.conversations_file)
            
            now = datetime.now()
            conversation = Conversation(
                id=conversation_id,
                title=title or f"Conversation {conversation_id[:8]}",
                created_at=now,
                updated_at=now,
                model=model
            )
            
            conversations[conversation_id] = {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "model": conversation.model
            }
            
            await self._write_json(self.conversations_file, conversations)
            return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        conversations = await self._read_json(self.conversations_file)
        conv_data = conversations.get(conversation_id)
        
        if conv_data:
            return Conversation(
                id=conv_data["id"],
                title=conv_data["title"],
                created_at=datetime.fromisoformat(conv_data["created_at"]),
                updated_at=datetime.fromisoformat(conv_data["updated_at"]),
                model=conv_data.get("model")
            )
        return None
    
    async def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """List all conversations"""
        conversations = await self._read_json(self.conversations_file)
        
        # Sort by updated_at descending
        sorted_convs = sorted(
            conversations.values(),
            key=lambda x: x["updated_at"],
            reverse=True
        )
        
        # Apply pagination
        paginated = sorted_convs[offset:offset + limit]
        
        return [
            Conversation(
                id=conv["id"],
                title=conv["title"],
                created_at=datetime.fromisoformat(conv["created_at"]),
                updated_at=datetime.fromisoformat(conv["updated_at"]),
                model=conv.get("model")
            )
            for conv in paginated
        ]
    
    async def add_message(self, message: Message) -> Message:
        """Add a message to a conversation"""
        async with self._lock:
            messages = await self._read_json(self.messages_file)
            conversations = await self._read_json(self.conversations_file)
            
            # Generate message ID
            message_id = len([m for msgs in messages.values() for m in msgs]) + 1
            message.id = message_id
            
            # Add message
            if message.conversation_id not in messages:
                messages[message.conversation_id] = []
            
            messages[message.conversation_id].append({
                "id": message.id,
                "conversation_id": message.conversation_id,
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "model": message.model
            })
            
            # Update conversation updated_at
            if message.conversation_id in conversations:
                conversations[message.conversation_id]["updated_at"] = datetime.now().isoformat()
            
            await self._write_json(self.messages_file, messages)
            await self._write_json(self.conversations_file, conversations)
            
            return message
    
    async def get_messages(self, conversation_id: str) -> List[Message]:
        """Get all messages for a conversation"""
        messages = await self._read_json(self.messages_file)
        conv_messages = messages.get(conversation_id, [])
        
        return [
            Message(
                id=msg["id"],
                conversation_id=msg["conversation_id"],
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"]),
                model=msg.get("model")
            )
            for msg in sorted(conv_messages, key=lambda x: x["timestamp"])
        ]
    
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear all messages in a conversation"""
        async with self._lock:
            messages = await self._read_json(self.messages_file)
            if conversation_id in messages:
                messages[conversation_id] = []
                await self._write_json(self.messages_file, messages)
        return True
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        async with self._lock:
            conversations = await self._read_json(self.conversations_file)
            messages = await self._read_json(self.messages_file)
            
            if conversation_id in conversations:
                del conversations[conversation_id]
            
            if conversation_id in messages:
                del messages[conversation_id]
            
            await self._write_json(self.conversations_file, conversations)
            await self._write_json(self.messages_file, messages)
        
        return True
    
    async def close(self) -> None:
        """Close database connection"""
        # No connections to close for JSON files
        pass
