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


class ChatResponse(BaseModel):
    response: str


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
            "session_id": "optional-user-id"
        }
    
    Response:
        {
            "response": "Mistral's response here"
        }
    """
    result = chat_handler.handle_query(
        user_query=request.query,
        session_id=request.session_id
    )
    
    return ChatResponse(response=result["response"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "YanaChat V2"}


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
