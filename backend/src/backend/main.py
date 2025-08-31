"""
FastAPI main application for AI Chat Backend
"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json

# Load environment variables
load_dotenv()

from .database.factory import DatabaseFactory
from .database.interface import DatabaseInterface, Message, Conversation
from .services.ollama_service import OllamaService

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: str = "phi3:mini"
    stream: bool = False
    enable_search: bool = False

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    model: str
    timestamp: datetime

class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    model: Optional[str]

class MessageResponse(BaseModel):
    id: Optional[int]
    conversation_id: str
    role: str
    content: str
    timestamp: datetime
    model: Optional[str]

class ModelInfo(BaseModel):
    name: str
    size: Optional[int] = None
    digest: Optional[str] = None
    modified_at: Optional[str] = None

# Global instances
app = FastAPI(
    title="AI Chat Backend",
    description="Backend API for AI Chat application using Ollama",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
db: DatabaseInterface = None
ollama_service: OllamaService = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global db, ollama_service

    # Initialize database with environment configuration
    db_type = os.getenv("DATABASE_TYPE", "sqlite")
    db_path = os.getenv("DATABASE_PATH", "data/conversations.db")

    if db_type == "sqlite":
        db = DatabaseFactory.create("sqlite", db_path=db_path)
    elif db_type == "json":
        db = DatabaseFactory.create("json", data_dir=os.path.dirname(db_path))
    elif db_type == "csv":
        db = DatabaseFactory.create("csv", data_dir=os.path.dirname(db_path))
    else:
        db = DatabaseFactory.create("sqlite", db_path=db_path)

    await db.initialize()

    # Initialize Ollama service
    ollama_service = OllamaService()

    print("AI Chat Backend started successfully!")
    print(f"Database: {db_type} at {db_path}")
    print(f"Ollama: {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db, ollama_service
    
    if db:
        await db.close()
    
    if ollama_service:
        ollama_service.close()
    
    print("AI Chat Backend shutdown complete!")

def get_db() -> DatabaseInterface:
    """Dependency to get database instance"""
    return db

def get_ollama_service() -> OllamaService:
    """Dependency to get Ollama service instance"""
    return ollama_service

def generate_conversation_title(message: str, max_length: int = 50) -> str:
    """Generate a conversation title from the first message"""
    # Remove extra whitespace and newlines
    clean_message = " ".join(message.strip().split())

    # If message is short enough, use it as is
    if len(clean_message) <= max_length:
        return clean_message

    # Truncate at word boundary
    words = clean_message.split()
    title = ""
    for word in words:
        if len(title + " " + word) <= max_length - 3:  # Leave space for "..."
            title += " " + word if title else word
        else:
            break

    return title + "..." if len(clean_message) > max_length else title

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Chat Backend API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/models", response_model=List[ModelInfo])
async def get_models(ollama: OllamaService = Depends(get_ollama_service)):
    """Get available models from Ollama"""
    try:
        models = await ollama.get_available_models()
        return [
            ModelInfo(
                name=model.get("name", model.get("model", "")),
                size=model.get("size"),
                digest=model.get("digest"),
                modified_at=str(model.get("modified_at")) if model.get("modified_at") else None
            )
            for model in models
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    database: DatabaseInterface = Depends(get_db),
    ollama: OllamaService = Depends(get_ollama_service)
):
    """Generate chat response"""
    try:
        # Use default model if none provided or empty
        model_to_use = request.model if request.model and request.model.strip() else "phi3:mini"

        # Create or get conversation
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # Check if conversation exists, if not create it
        conversation = await database.get_conversation(conversation_id)
        if not conversation:
            # Generate title from the first message
            title = generate_conversation_title(request.message)
            conversation = await database.create_conversation(
                conversation_id=conversation_id,
                title=title,
                model=model_to_use
            )
        
        # Get conversation history
        messages = await database.get_messages(conversation_id)
        
        # Convert to Ollama format
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add new user message
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            timestamp=datetime.now(),
            model=model_to_use
        )
        await database.add_message(user_message)

        ollama_messages.append({
            "role": "user",
            "content": request.message
        })

        # Get response from Ollama
        if request.stream:
            # For streaming, we'll handle it differently
            raise HTTPException(status_code=501, detail="Streaming not implemented in this endpoint")

        # Use enhanced chat if search is enabled
        if request.enable_search:
            response = await ollama.enhanced_chat(
                model=model_to_use,
                messages=ollama_messages,
                enable_search=True,
                stream=False
            )
        else:
            response = await ollama.chat(
                model=model_to_use,
                messages=ollama_messages,
                stream=False
            )

        assistant_content = response.get("message", {}).get("content", "")

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_content,
            timestamp=datetime.now(),
            model=model_to_use
        )
        await database.add_message(assistant_message)

        return ChatResponse(
            response=assistant_content,
            conversation_id=conversation_id,
            model=model_to_use,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@app.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    limit: int = 50,
    offset: int = 0,
    database: DatabaseInterface = Depends(get_db)
):
    """Get list of conversations"""
    try:
        conversations = await database.list_conversations(limit=limit, offset=offset)
        return [
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                model=conv.model
            )
            for conv in conversations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversations: {str(e)}")

@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    database: DatabaseInterface = Depends(get_db)
):
    """Get a specific conversation"""
    try:
        conversation = await database.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            model=conversation.model
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversation: {str(e)}")

@app.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    database: DatabaseInterface = Depends(get_db)
):
    """Get messages for a conversation"""
    try:
        messages = await database.get_messages(conversation_id)
        return [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                model=msg.model
            )
            for msg in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting messages: {str(e)}")

@app.delete("/conversations/{conversation_id}/messages")
async def clear_conversation(
    conversation_id: str,
    database: DatabaseInterface = Depends(get_db)
):
    """Clear all messages in a conversation"""
    try:
        success = await database.clear_conversation(conversation_id)
        if success:
            return {"message": "Conversation cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear conversation")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    database: DatabaseInterface = Depends(get_db)
):
    """Delete a conversation and all its messages"""
    try:
        success = await database.delete_conversation(conversation_id)
        if success:
            return {"message": "Conversation deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

@app.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    title_data: dict,
    database: DatabaseInterface = Depends(get_db)
):
    """Update conversation title"""
    try:
        # This would require adding an update_title method to the database interface
        # For now, we'll generate titles automatically from the first message
        return {"message": "Title update not implemented yet"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating title: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
