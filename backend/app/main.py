from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_db
from app.api.api_router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Team Building Portal - Backend API for managing team building events",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("\n" + "=" * 60)
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION}")
    print("=" * 60)

    # Init database (tạo tables + seed admin nếu chưa có)
    init_db()

    print("=" * 60)
    print(f"✅ Server started successfully!")
    print(f"📚 API Documentation: http://localhost:8000/api/docs")
    print(f"🔐 Default Admin: admin@company.com / Admin@123456")
    print("=" * 60 + "\n")


@app.get("/", tags=["health"])
async def root():
    """Root endpoint - API health check"""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/api/docs"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}


# Include API router
app.include_router(api_router, prefix="/api/v1")
