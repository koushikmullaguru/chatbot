from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .core.config import settings
from .core.database import engine, get_db
from .api.main import api_router
from .models import *  # Import all models to create tables

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI School Chat Application",
    description="Backend API for AI School Chat Application",
    version="1.0.0",
    openapi_url=f"/api/v1/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "AI School Chat Application API is running"}


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}