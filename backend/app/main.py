import uuid
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.agent.graph import run_agent
from app.models.schemas import ChatRequest, ChatResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.groq_api_key:
        print("WARNING: GROQ_API_KEY not set. The agent needs a Groq API key (free at console.groq.com).")
    if not settings.tavily_api_key:
        print("WARNING: TAVILY_API_KEY not set. Web search will be limited.")
    yield


app = FastAPI(title="Travel Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())

    if not settings.groq_api_key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY not configured. Set it in backend/.env",
        )

    try:
        result = await run_agent(req.message, session_id)
        return ChatResponse(
            session_id=session_id,
            message=result.get("response_message", ""),
            destinations=result.get("destinations", []),
        )
    except Exception as e:
        traceback.print_exc()
        err_str = str(e)
        if "429" in err_str or "quota" in err_str or "rate limit" in err_str.lower():
            return ChatResponse(
                session_id=session_id,
                message=(
                    "⚠️ **Error de conexión con Groq.**\n\n"
                    "La API key de Groq tiene la cuota agotada o hay muchas solicitudes. "
                    "Consigue una key gratuita en https://console.groq.com\n\n"
                    "⚠️ **Groq connection error.** The API key has exceeded its quota. "
                    "Get a free key at https://console.groq.com"
                ),
                destinations=[],
            )
        return ChatResponse(
            session_id=session_id,
            message=(
                "Lo siento, ocurrió un error inesperado. Intenta de nuevo más tarde.\n\n"
                "Sorry, an unexpected error occurred. Please try again later."
            ),
            destinations=[],
        )
