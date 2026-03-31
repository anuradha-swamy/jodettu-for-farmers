from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
import os
from typing import List
import asyncio

# Import only lightweight modules at startup
from app.config import settings

# Initialize FastAPI app FIRST - before any heavy imports
app = FastAPI(
    title="Jodettu API",
    version="1.0.0",
    description="Jodettu API with Animal Recognition",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Jodettu API",
        version="1.0.0",
        description="API docs with JWT Auth and Animal Recognition",
        routes=app.routes,
    )
    
    # Add JWT security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Apply security to all endpoints except specific public ones
    public_paths = ["/analyze", "/api/v1/animals/classify", "/api/v1/animals/health", "/health", "/"]
    
    for path in openapi_schema["paths"]:
        if path not in public_paths:
            for method in openapi_schema["paths"][path]:
                if method.lower() != "options":
                    openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Health check endpoint - available immediately
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Jodettu API is running"}

@app.get("/")
def read_root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message":"CORS enabled! Jodettu API is running"}

# Lazy loading function for all routes and services
async def initialize_services():
    """Initialize all heavy services after FastAPI startup"""
    print("🔄 Initializing services...")
    
    # 1. Initialize Database (with timeout)
    try:
        from general.database import init_db
        await asyncio.wait_for(init_db(), timeout=10.0)
        print("✅ Database initialized.")
    except asyncio.TimeoutError:
        print("⚠️ Database initialization timed out, but server continues...")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}, but server continues...")
    
    # 2. Include animal routes (lightweight)
    try:
        from routes.animal_routes import router as animal_router
        app.include_router(animal_router, prefix="/Jodettu/Animals", tags=["OWN ANIMALS"])
        print("✅ Animal routes included.")
    except Exception as e:
        print(f"⚠️ Failed to include animal routes: {e}")
    
    # 3. Include machine routes (lightweight)
    try:
        from routes.machine_routes import router as machine_router
        app.include_router(machine_router, prefix="/Jodettu/Machines", tags=["MACHINES"])
        print("✅ Machine routes included.")
    except Exception as e:
        print(f"⚠️ Failed to include machine routes: {e}")
    
    # 4. Include market routes (lightweight)
    try:
        from routes.feed_medicine_routes import router as market_router
        app.include_router(market_router, prefix="/Jodettu/Market", tags=["MARKET"])
        print("✅ Market routes included.")
    except Exception as e:
        print(f"⚠️ Failed to include market routes: {e}")
    
    # 5. Include auth routes (lightweight)
    try:
        from routes.login_routes import router as login_router
        app.include_router(login_router, prefix="/Jodettu/Auth", tags=["Authentication"])
        print("✅ Auth routes included.")
    except Exception as e:
        print(f"⚠️ Failed to include auth routes: {e}")
    
    # 6. Include ML classification routes (heavy - loaded last)
    try:
        from app.routes.animal_classification import router as animal_classification_router
        app.include_router(animal_classification_router)
        print("✅ ML classification routes included.")
    except Exception as e:
        print(f"⚠️ Failed to include ML routes: {e}")
    
    print("🚀 All services initialized. Server fully ready.")

@app.on_event("startup")
async def startup():
    """
    FastAPI startup event - completes immediately
    Heavy initialization happens in background
    """
    print("🚀 FastAPI starting up...")
    
    # Start heavy initialization in background but don't wait for it
    asyncio.create_task(initialize_services())
    
    print("✅ FastAPI startup complete. Server accepting connections.")
    print("📝 Heavy services initializing in background...")

# Optional: Add endpoint to check initialization status
initialization_status = {"status": "starting", "services": {}}

@app.get("/init-status")
async def get_init_status():
    """Check initialization status"""
    return initialization_status
