from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
from database import create_table_if_not_exists
from routes.auth_routes import router as auth_router
from routes.health_routes import router as health_router
from routes.location_routes import router as location_router
from routes.gamification_routes import router as gamification_router

load_dotenv()

app = FastAPI(
    title="Remedi API",
    description="Backend API for the Remedi mobile app",
    version="1.0.0"
)

# Custom validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("=" * 80)
    print("VALIDATION ERROR:")
    print(f"URL: {request.url}")
    print(f"Method: {request.method}")
    print(f"Errors: {exc.errors()}")
    try:
        body = await request.body()
        print(f"Request body: {body.decode()}")
    except:
        pass
    print("=" * 80)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )

# Configure CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your mobile app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("Starting Remedi API...")
    create_table_if_not_exists()
    print("Remedi API ready!")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Remedi API is running",
        "version": "1.0.0"
    }

# Include routers
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(location_router)
app.include_router(gamification_router)

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "services": {
            "fda_api": "configured",
            "openai": "configured",
            "openstreetmap": "available"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
