"""
SQLite implementation of the database interface
"""
import aiosqlite
import json
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from .interface import DatabaseInterface, Message, Conversation


class SQLiteDatabase(DatabaseInterface):
    def __init__(self, db_path: str = "data/conversations.db"):
        self.db_path = db_path
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> None:
        """Initialize SQLite database with tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    model TEXT
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    model TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            
            await db.commit()
    
    async def create_conversation(self, conversation_id: str, title: str = None, model: str = None) -> Conversation:
        """Create a new conversation"""
        now = datetime.now().isoformat()
        conversation = Conversation(
            id=conversation_id,
            title=title or f"Conversation {conversation_id[:8]}",
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
            model=model
        )
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at, model) VALUES (?, ?, ?, ?, ?)",
                (conversation.id, conversation.title, now, now, conversation.model)
            )
            await db.commit()
        
        return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, title, created_at, updated_at, model FROM conversations WHERE id = ?",
                (conversation_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Conversation(
                        id=row[0],
                        title=row[1],
                        created_at=datetime.fromisoformat(row[2]),
                        updated_at=datetime.fromisoformat(row[3]),
                        model=row[4]
                    )
        return None
    
    async def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """List all conversations"""
        conversations = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, title, created_at, updated_at, model FROM conversations ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ) as cursor:
                async for row in cursor:
                    conversations.append(Conversation(
                        id=row[0],
                        title=row[1],
                        created_at=datetime.fromisoformat(row[2]),
                        updated_at=datetime.fromisoformat(row[3]),
                        model=row[4]
                    ))
        return conversations
    
    async def add_message(self, message: Message) -> Message:
        """Add a message to a conversation"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO messages (conversation_id, role, content, timestamp, model) VALUES (?, ?, ?, ?, ?)",
                (message.conversation_id, message.role, message.content, message.timestamp.isoformat(), message.model)
            )
            message.id = cursor.lastrowid
            
            # Update conversation updated_at
            await db.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), message.conversation_id)
            )
            await db.commit()
        
        return message
    
    async def get_messages(self, conversation_id: str) -> List[Message]:
        """Get all messages for a conversation"""
        messages = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, conversation_id, role, content, timestamp, model FROM messages WHERE conversation_id = ? ORDER BY timestamp",
                (conversation_id,)
            ) as cursor:
                async for row in cursor:
                    messages.append(Message(
                        id=row[0],
                        conversation_id=row[1],
                        role=row[2],
                        content=row[3],
                        timestamp=datetime.fromisoformat(row[4]),
                        model=row[5]
                    ))
        return messages
    
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear all messages in a conversation"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            await db.commit()
        return True
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            await db.commit()
        return True
    
    async def close(self) -> None:
        """Close database connection"""
        # SQLite connections are closed automatically
        pass
