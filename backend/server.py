from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# from google import genai
import os
# from dotenv import load_dotenv
from typing import Optional, List, Dict, AsyncGenerator
import uuid
import json
import logging
from pathlib import Path
import boto3
import asyncio


from langchain_google_genai import ChatGoogleGenerativeAI

from context import prompt
from cache import semantic_cache, log_cache_hit, log_cache_miss, log_cache_store, get_cache_performance_metrics, get_cache_health_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        # other params...
    )
    logger.info("LLM initialized successfully")
except Exception as e:
    logger.error(f"Error initializing LLM: {e}")
    llm = None



app = FastAPI()

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Google AI client
# try:
#     client = genai.Client()
#     logger.info("Google AI client initialized successfully")
# except Exception as e:
#     logger.error(f"Error initializing Google AI client: {e}")
#     client = None


# Memory storage configuration
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
S3_BUCKET = os.getenv("S3_BUCKET", "")
MEMORY_DIR = os.getenv("MEMORY_DIR", "../memory")

# Initialize S3 client if needed
if USE_S3:
    s3_client = boto3.client("s3")


# Memory management functions
def get_memory_path(session_id: str) -> str:
    return f"{session_id}.json"
# Memory functions
def load_conversation(session_id: str) -> List[Dict]:
    """Load conversation history from file"""
    if USE_S3:
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=get_memory_path(session_id))
            return json.loads(response["Body"].read().decode("utf-8"))
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return []
            raise
    else:
        # Local file storage
        file_path = os.path.join(MEMORY_DIR, get_memory_path(session_id))
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return []


def save_conversation(session_id: str, messages: List[Dict]):
    """Save conversation history to storage"""
    if USE_S3:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=get_memory_path(session_id),
            Body=json.dumps(messages, indent=2),
            ContentType="application/json",
        )
    else:
        # Local file storage
        os.makedirs(MEMORY_DIR, exist_ok=True)
        file_path = os.path.join(MEMORY_DIR, get_memory_path(session_id))
        with open(file_path, "w") as f:
            json.dump(messages, f, indent=2)






# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.get("/")
async def root():
    return {
        "message": "AI Digital Twin API",
        "memory_enabled": True,
        "storage": "S3" if USE_S3 else "local",
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "use_s3": USE_S3}


@app.post("/chat")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        logger.info(f"Processing streaming chat request for session: {session_id}")
        
        # Check cache first
        cached_response = semantic_cache.search_similar(request.message)
        if cached_response:
            log_cache_hit(request.message, "semantic_cache")
            
            async def generate_cached_response() -> AsyncGenerator[str, None]:
                """Generate streaming response from cache"""
                try:
                    # Simulate streaming for cached response
                    for char in cached_response:
                        yield f"data: {json.dumps({'content': char, 'session_id': session_id, 'cached': True})}\n\n"
                        await asyncio.sleep(0.01)
                    
                    # Update conversation history
                    conversation = load_conversation(session_id)
                    conversation.append({"role": "user", "content": request.message})
                    conversation.append({"role": "assistant", "content": cached_response})
                    save_conversation(session_id, conversation)
                    
                    yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'cached': True})}\n\n"
                    
                except Exception as e:
                    logger.error(f"Error in cached streaming response: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                generate_cached_response(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        
        log_cache_miss(request.message)
        
        conversation = load_conversation(session_id)
        # Build messages with history
        messages = [{"role": "system", "content": prompt()}]
        
        # Add conversation history
        for msg in conversation:
            messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": request.message})
        logger.info(f"Sending {len(messages)} messages to LLM for streaming")

        async def generate_stream() -> AsyncGenerator[str, None]:
            """Generate streaming response"""
            try:
                if llm is None:
                    yield f"data: {json.dumps({'error': 'LLM not initialized properly'})}\n\n"
                    return
                
                # Get streaming response from LLM
                response_content = ""
                
                # Use the stream method if available, otherwise fall back to invoke and simulate streaming
                if hasattr(llm, 'astream'):
                    async for chunk in llm.astream(messages):
                        if hasattr(chunk, 'content') and chunk.content:
                            # Stream each token/character as it comes
                            for char in chunk.content:
                                response_content += char
                                yield f"data: {json.dumps({'content': char, 'session_id': session_id, 'cached': False})}\n\n"
                                await asyncio.sleep(0.01)  # Small delay for token-level streaming effect
                else:
                    # Fallback to regular invoke and simulate streaming
                    response = llm.invoke(messages)
                    response_content = response.text
                    
                    # Simulate token-level streaming by sending individual characters
                    for char in response.text:
                        yield f"data: {json.dumps({'content': char, 'session_id': session_id, 'cached': False})}\n\n"
                        await asyncio.sleep(0.001)  # Small delay to simulate streaming
                
                # Store in cache
                semantic_cache.store(request.message, response_content)
                log_cache_store(request.message, len(response_content))
                
                # Update conversation history with the complete response
                conversation.append({"role": "user", "content": request.message})
                conversation.append({"role": "assistant", "content": response_content})
                
                # Save updated conversation
                save_conversation(session_id, conversation)
                
                # Send completion signal
                yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'cached': False})}\n\n"
                
                logger.info(f"Streaming chat response sent for session: {session_id}")
                
            except Exception as e:
                logger.error(f"Error in streaming response: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in streaming chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/sessions")
async def list_sessions():
    """List all conversation sessions"""
    sessions = []
    memory_path = Path(MEMORY_DIR)
    if not memory_path.exists():
        memory_path.mkdir(parents=True, exist_ok=True)
    
    for file_path in memory_path.glob("*.json"):
        session_id = file_path.stem
        with open(file_path, "r", encoding="utf-8") as f:
            conversation = json.load(f)
            sessions.append({
                "session_id": session_id,
                "message_count": len(conversation),
                "last_message": conversation[-1]["content"] if conversation else None
            })
    return {"sessions": sessions}

@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Retrieve conversation history"""
    try:
        conversation = load_conversation(session_id)
        return {"session_id": session_id, "messages": conversation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        return semantic_cache.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/health")
async def cache_health_check():
    """Check cache health status"""
    try:
        return get_cache_health_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cache/clear")
async def clear_cache():
    """Clear all cache entries"""
    try:
        success = semantic_cache.clear()
        return {"success": success, "message": "Cache cleared" if success else "Failed to clear cache"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/performance")
async def get_cache_performance():
    """Get comprehensive cache performance metrics"""
    try:
        return get_cache_performance_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)