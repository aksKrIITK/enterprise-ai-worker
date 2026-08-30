from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.approvals import router as approvals_router
from app.api.evals import router as evals_router
from app.logging_config import setup_logging
from app.middleware import TraceAndLoggingMiddleware
from app.error_handlers import register_exception_handlers

# Setup global structured JSON logging
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register custom exception handlers (RFC 7807)
register_exception_handlers(app)

# Add Middleware
app.add_middleware(TraceAndLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(approvals_router)
app.include_router(evals_router)


@app.get("/")
async def root():
    return {"message": "Enterprise AI Orchestration Service Online", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)

