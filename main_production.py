"""
Production-ready FastAPI main application.
This module initializes both MongoDB (transactional data) and PostgreSQL (master data) connections.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import asyncio
import os

# Load environment variables at the very beginning
load_dotenv()

# Import database initialization
from db.async_db import init_postgres_db, close_postgres_db
from services.master_data_service import MasterDataService

# Import routers after env vars are loaded
from routes.animal_routes_fixed import router as animal_router
from routes.machine_routes import router as machine_router
from routes.feed_medicine_routes import router as market_router
from routes.login_routes import router as login_router
from app.routes.animal_classification import router as animal_classification_router, get_classifier


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events for both databases.
    """
    # Startup
    print("STARTING: Starting up Jodettu API...")
    
    try:
        # Initialize PostgreSQL (master data)
        print("INITIALIZING: PostgreSQL database...")
        await init_postgres_db()
        print("SUCCESS: PostgreSQL database initialized.")
        
        # Initialize default master data if needed
        print("INITIALIZING: Default master data...")
        from db.async_db import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await MasterDataService.initialize_default_data(db)
        print("SUCCESS: Default master data initialized.")
        
        # MongoDB is already initialized eagerly at import time
        print("SUCCESS: MongoDB connection handled at import time.")
        
        # Load ML Model in the background
        print("LOADING: ML Model...")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, get_classifier)
        print("SUCCESS: ML Model pre-loaded.")
        
        print("READY: Server is ready to accept requests.")
        
    except Exception as e:
        print(f"ERROR: Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    print("SHUTTING DOWN: Closing database connections...")
    try:
        await close_postgres_db()
        print("SUCCESS: PostgreSQL connection closed.")
        # MongoDB connection will be closed automatically when the process exits
        print("SUCCESS: Shutdown complete.")
    except Exception as e:
        print(f"ERROR: Error during shutdown: {e}")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Jodettu API",
    version="1.0.0",
    description="Jodettu API with Animal Recognition - Production Ready",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(animal_router, prefix="/Jodettu/Animals", tags=["OWN ANIMALS"])
app.include_router(machine_router, prefix="/Jodettu/Machines", tags=["MACHINES"])
app.include_router(market_router, prefix="/Jodettu/Market", tags=["MARKET"])
app.include_router(login_router, prefix="/Jodettu/Auth", tags=["Authentication"])
app.include_router(animal_classification_router, tags=["Animal Classification"])


@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Jodettu API",
        "version": "1.0.0",
        "status": "running",
        "databases": {
            "mongodb": "transactional_data",
            "postgresql": "master_data"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "services": {
            "mongodb": "connected",
            "postgresql": "connected",
            "ml_model": "loaded"
        }
    }


@app.get("/info")
def api_info():
    """API information endpoint."""
    return {
        "name": "Jodettu API",
        "description": "Livestock management system with AI-powered animal recognition",
        "version": "1.0.0",
        "features": [
            "Animal management (MongoDB)",
            "Master data management (PostgreSQL)",
            "AI-powered animal classification",
            "Market functionality",
            "User authentication",
            "Vaccination tracking"
        ],
        "endpoints": {
            "animals": "/Jodettu/Animals",
            "machines": "/Jodettu/Machines",
            "market": "/Jodettu/Market",
            "auth": "/Jodettu/Auth",
            "classification": "/classify"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Run the application
    uvicorn.run(
        "main_production:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )
