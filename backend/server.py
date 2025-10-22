from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
import os
# from dotenv import load_dotenv
from typing import Optional, List, Dict
import uuid
import json
import logging
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI

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
try:
    client = genai.Client()
    logger.info("Google AI client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Google AI client: {e}")
    client = None

# Memory directory
MEMORY_DIR = Path("../memory")
MEMORY_DIR.mkdir(exist_ok=True)


# Load personality details
def load_personality():
    try:
        with open("me.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Error loading personality file: {e}")
        return "You are a helpful AI assistant."


try:
    PERSONALITY = load_personality()
    logger.info("Personality loaded successfully")
except Exception as e:
    logger.error(f"Failed to load personality: {e}")
    PERSONALITY = "You are a helpful AI assistant."

# Memory functions
def load_conversation(session_id: str) -> List[Dict]:
    """Load conversation history from file"""
    try:
        file_path = MEMORY_DIR / f"{session_id}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading conversation {session_id}: {e}")
        return []


def save_conversation(session_id: str, messages: List[Dict]):
    """Save conversation history to file"""
    try:
        file_path = MEMORY_DIR / f"{session_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving conversation {session_id}: {e}")


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.get("/")
async def root():
    return {"message": "AI Digital Twin API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        logger.info(f"Processing chat request for session: {session_id}")
        
        conversation = load_conversation(session_id)
        # Build messages with history
        messages = [{"role": "system", "content": PERSONALITY}]
        
        # Add conversation history
        for msg in conversation:
            messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": request.message})
        logger.info(f"Sending {len(messages)} messages to LLM")

        # Call Gemini API
        try:
            if llm is None:
                raise Exception("LLM not initialized properly")
            response = llm.invoke(messages)
            logger.info("LLM response received successfully")
        except Exception as llm_error:
            logger.error(f"LLM invocation error: {llm_error}")
            raise HTTPException(status_code=500, detail=f"LLM error: {str(llm_error)}")

        # Update conversation history
        conversation.append({"role": "user", "content": request.message})
        conversation.append({"role": "assistant", "content": response.text})
        
        # Save updated conversation
        save_conversation(session_id, conversation)
        
        logger.info(f"Chat response sent for session: {session_id}")
        return ChatResponse(
            response=response.text,
            session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/sessions")
async def list_sessions():
    """List all conversation sessions"""
    sessions = []
    for file_path in MEMORY_DIR.glob("*.json"):
        session_id = file_path.stem
        with open(file_path, "r", encoding="utf-8") as f:
            conversation = json.load(f)
            sessions.append({
                "session_id": session_id,
                "message_count": len(conversation),
                "last_message": conversation[-1]["content"] if conversation else None
            })
    return {"sessions": sessions}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)