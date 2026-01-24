import os
from typing import Optional
from dotenv import load_dotenv

from fastapi import FastAPI

load_dotenv()
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.chat_handler import ChatHandler


# Initialize FastAPI app
app = FastAPI(
    title="YanaChat V2",
    description="Mistral-powered chatbot with JSONL logging",
    version="1.0.0"
)

# Initialize chat handler
chat_handler = ChatHandler()


# Request/Response models
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    web_search: Optional[bool] = False


class ChatResponse(BaseModel):
    response: str


class ClearHistoryRequest(BaseModel):
    session_id: str


# Mount static files
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


# Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the chat UI."""
    try:
        with open("app/static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <body>
                <h1>YanaChat V2</h1>
                <p>UI not yet implemented. Use POST /api/chat to interact.</p>
            </body>
        </html>
        """


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.
    
    Request:
        {
            "query": "Your question here",
            "session_id": "optional-user-id",
            "web_search": false
        }
    
    Response:
        {
            "response": "Mistral's response here"
        }
    """
    result = chat_handler.handle_query(
        user_query=request.query,
        session_id=request.session_id,
        use_web_search=request.web_search
    )
    
    return ChatResponse(response=result["response"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "YanaChat V2"}


@app.post("/api/clear_history")
async def clear_history(request: ClearHistoryRequest):
    """
    Clear conversation history for a session.
    
    Request:
        {
            "session_id": "session-to-clear"
        }
    
    Response:
        {
            "status": "ok",
            "message": "History cleared for session: session-to-clear"
        }
    """
    chat_handler.clear_session_history(request.session_id)
    return {
        "status": "ok",
        "message": f"History cleared for session: {request.session_id}"
    }


@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """
    Get conversation history for a session.
    
    Response:
        {
            "session_id": "session-id",
            "history": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ],
            "message_count": 4
        }
    """
    history = chat_handler.get_session_history(session_id)
    return {
        "session_id": session_id,
        "history": history,
        "message_count": len(history)
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
