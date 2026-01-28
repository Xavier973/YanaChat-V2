import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict
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


class ReportRequest(BaseModel):
    session_id: str
    user_message: str
    conversation: List[Dict[str, str]]


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
    try:
        result = chat_handler.handle_query(
            user_query=request.query,
            session_id=request.session_id,
            use_web_search=request.web_search
        )
        
        return ChatResponse(response=result["response"])
    except Exception as e:
        # Log l'erreur et retourner une réponse d'erreur propre
        import traceback
        error_msg = f"Erreur interne du serveur: {str(e)}"
        print(f"Error in /api/chat: {traceback.format_exc()}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=error_msg)


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


@app.post("/api/report")
async def report_conversation(request: ReportRequest):
    """
    Report a problematic conversation via email.
    
    Request:
        {
            "session_id": "session-id",
            "user_message": "Description du problème",
            "conversation": [{"role": "user", "content": "..."}]
        }
    
    Response:
        {
            "status": "ok",
            "message": "Report sent successfully"
        }
    """
    # Configuration SMTP depuis .env
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    report_email = os.getenv("REPORT_EMAIL", "x.cuniberti@gmail.com")
    
    # Vérifier configuration SMTP
    if not smtp_user or not smtp_password:
        return {
            "status": "error",
            "message": "SMTP not configured. Please set SMTP_USER and SMTP_PASSWORD in .env"
        }
    
    # Construire le contenu de l'email
    conversation_text = "\n\n".join([
        f"**{msg['role'].upper()}**: {msg['content']}"
        for msg in request.conversation
    ])
    
    email_body = f"""
    === SIGNALEMENT YANACHAT ===
    
    Session ID: {request.session_id}
    
    MESSAGE UTILISATEUR:
    {request.user_message}
    
    =============================
    CONVERSATION COMPLÈTE:
    =============================
    
    {conversation_text}
    
    =============================
    Envoyé automatiquement depuis YanaChat V2
    """
    
    try:
        # Créer le message email
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = report_email
        msg['Subject'] = f"[YanaChat] Signalement - Session {request.session_id[:8]}"
        
        msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
        
        # Envoyer l'email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return {
            "status": "ok",
            "message": "Report sent successfully"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send report: {str(e)}"
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
