import os
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routes import generate
from app.config import settings
from app.models.schemas import HealthResponse

# Configure structured logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("github_card_backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Initializing GitHub Card Generator Backend...")
    os.makedirs(settings.CARDS_DIR, exist_ok=True)
    logger.info(f"Static cards directory verified: {settings.CARDS_DIR}")
    yield
    # Shutdown logic
    logger.info("Shutting down GitHub Card Generator Backend...")

app = FastAPI(
    title="Premium AI GitHub Card Generator",
    description="Production-grade API for generating high-end developer showcase cards using Gemini 2.5 Flash and Google ADK.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.2f}s")
    return response

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "An unexpected error occurred. Please try again later."}
    )

# Static File Serving
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# API Routes
app.include_router(generate.router, prefix="/api", tags=["generation"])

@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """
    Check the health status of the API service.
    """
    return HealthResponse(status="healthy", version="1.0.0")

if __name__ == "__main__":
    import uvicorn
    # Using settings for host and port
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
