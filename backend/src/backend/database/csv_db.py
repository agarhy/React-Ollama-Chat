"""
CSV file implementation of the database interface
"""
import pandas as pd
import asyncio
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from .interface import DatabaseInterface, Message, Conversation


class CSVDatabase(DatabaseInterface):
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.conversations_file = self.data_dir / "conversations.csv"
        self.messages_file = self.data_dir / "messages.csv"
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize CSV files"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.conversations_file.exists():
            conversations_df = pd.DataFrame(columns=['id', 'title', 'created_at', 'updated_at', 'model'])
            conversations_df.to_csv(self.conversations_file, index=False)
        
        if not self.messages_file.exists():
            messages_df = pd.DataFrame(columns=['id', 'conversation_id', 'role', 'content', 'timestamp', 'model'])
            messages_df.to_csv(self.messages_file, index=False)
    
    async def _read_conversations_df(self) -> pd.DataFrame:
        """Read conversations CSV"""
        try:
            return pd.read_csv(self.conversations_file)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return pd.DataFrame(columns=['id', 'title', 'created_at', 'updated_at', 'model'])
    
    async def _read_messages_df(self) -> pd.DataFrame:
        """Read messages CSV"""
        try:
            return pd.read_csv(self.messages_file)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return pd.DataFrame(columns=['id', 'conversation_id', 'role', 'content', 'timestamp', 'model'])
    
    async def create_conversation(self, conversation_id: str, title: str = None, model: str = None) -> Conversation:
        """Create a new conversation"""
        async with self._lock:
            conversations_df = await self._read_conversations_df()
            
            now = datetime.now()
            conversation = Conversation(
                id=conversation_id,
                title=title or f"Conversation {conversation_id[:8]}",
                created_at=now,
                updated_at=now,
                model=model
            )
            
            new_row = pd.DataFrame([{
                'id': conversation.id,
                'title': conversation.title,
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat(),
                'model': conversation.model
            }])
            
            conversations_df = pd.concat([conversations_df, new_row], ignore_index=True)
            conversations_df.to_csv(self.conversations_file, index=False)
            
            return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        conversations_df = await self._read_conversations_df()
        conv_row = conversations_df[conversations_df['id'] == conversation_id]
        
        if not conv_row.empty:
            row = conv_row.iloc[0]
            return Conversation(
                id=row['id'],
                title=row['title'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']),
                model=row['model'] if pd.notna(row['model']) else None
            )
        return None
    
    async def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """List all conversations"""
        conversations_df = await self._read_conversations_df()
        
        # Sort by updated_at descending
        conversations_df['updated_at_dt'] = pd.to_datetime(conversations_df['updated_at'])
        conversations_df = conversations_df.sort_values('updated_at_dt', ascending=False)
        
        # Apply pagination
        paginated_df = conversations_df.iloc[offset:offset + limit]
        
        conversations = []
        for _, row in paginated_df.iterrows():
            conversations.append(Conversation(
                id=row['id'],
                title=row['title'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']),
                model=row['model'] if pd.notna(row['model']) else None
            ))
        
        return conversations
    
    async def add_message(self, message: Message) -> Message:
        """Add a message to a conversation"""
        async with self._lock:
            messages_df = await self._read_messages_df()
            conversations_df = await self._read_conversations_df()
            
            # Generate message ID
            message_id = len(messages_df) + 1
            message.id = message_id
            
            # Add message
            new_message = pd.DataFrame([{
                'id': message.id,
                'conversation_id': message.conversation_id,
                'role': message.role,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'model': message.model
            }])
            
            messages_df = pd.concat([messages_df, new_message], ignore_index=True)
            messages_df.to_csv(self.messages_file, index=False)
            
            # Update conversation updated_at
            conv_mask = conversations_df['id'] == message.conversation_id
            if conv_mask.any():
                conversations_df.loc[conv_mask, 'updated_at'] = datetime.now().isoformat()
                conversations_df.to_csv(self.conversations_file, index=False)
            
            return message
    
    async def get_messages(self, conversation_id: str) -> List[Message]:
        """Get all messages for a conversation"""
        messages_df = await self._read_messages_df()
        conv_messages = messages_df[messages_df['conversation_id'] == conversation_id]
        
        # Sort by timestamp
        conv_messages['timestamp_dt'] = pd.to_datetime(conv_messages['timestamp'])
        conv_messages = conv_messages.sort_values('timestamp_dt')
        
        messages = []
        for _, row in conv_messages.iterrows():
            messages.append(Message(
                id=int(row['id']),
                conversation_id=row['conversation_id'],
                role=row['role'],
                content=row['content'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                model=row['model'] if pd.notna(row['model']) else None
            ))
        
        return messages
    
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear all messages in a conversation"""
        async with self._lock:
            messages_df = await self._read_messages_df()
            messages_df = messages_df[messages_df['conversation_id'] != conversation_id]
            messages_df.to_csv(self.messages_file, index=False)
        return True
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        async with self._lock:
            conversations_df = await self._read_conversations_df()
            messages_df = await self._read_messages_df()
            
            # Remove conversation
            conversations_df = conversations_df[conversations_df['id'] != conversation_id]
            conversations_df.to_csv(self.conversations_file, index=False)
            
            # Remove messages
            messages_df = messages_df[messages_df['conversation_id'] != conversation_id]
            messages_df.to_csv(self.messages_file, index=False)
        
        return True
    
    async def close(self) -> None:
        """Close database connection"""
        # No connections to close for CSV files
        pass
