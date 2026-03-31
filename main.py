from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import asyncio

# Load environment variables at the very beginning
load_dotenv()

# Import routers after env vars are loaded
# --- FIX: Reverted to original route file which now has the fix ---
from routes.animal_routes import router as animal_router
from routes.machine_routes import router as machine_router
from routes.feed_medicine_routes import router as market_router
from routes.login_routes import router as login_router
from routes.ai_routes import router as ai_router
from routes.enhanced_ai_routes import router as enhanced_ai_router
from routes.notification_routes import router as notification_router
from routes.product_routes import router as product_router
from routes.wishlist_routes import router as wishlist_router
from app.routes.animal_classification import router as animal_classification_router, get_classifier
from app.routes.animal_classification_enhanced import router as animal_classification_enhanced_router

# Import scheduler service
from services.scheduler_service import start_scheduler, stop_scheduler

# Initialize FastAPI app
app = FastAPI(
    title="Jodettu API",
    version="1.0.0",
    description="Jodettu API with Animal Recognition, AI Services, Location Services, and Translation",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(animal_router, prefix="/Jodettu/Animals", tags=["OWN ANIMALS"])
app.include_router(machine_router, prefix="/Jodettu/Machines", tags=["MACHINES"])
app.include_router(market_router, prefix="/Jodettu/Market", tags=["MARKET"])
app.include_router(login_router, prefix="/Jodettu/Auth", tags=["Authentication"])
app.include_router(notification_router, prefix="/Jodettu/Notifications", tags=["NOTIFICATIONS"])
app.include_router(ai_router, prefix="/Jodettu", tags=["AI Services"])
app.include_router(enhanced_ai_router, prefix="/Jodettu", tags=["Enhanced AI Services"])
app.include_router(product_router, prefix="/Jodettu/Products", tags=["PRODUCTS"])
app.include_router(wishlist_router, prefix="/Jodettu/Wishlist", tags=["WISHLIST"])
app.include_router(animal_classification_router)
app.include_router(animal_classification_enhanced_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Jodettu API"}

@app.on_event("startup")
async def startup_event():
    """
    Startup event to load ML models.
    MongoDB connection is now handled eagerly at import time.
    """
    print("Starting up Jodettu API...")
    print("MongoDB connection handled at import time.")
    
    # Load ML Models in the background
    loop = asyncio.get_event_loop()
    
    # Load existing animal classifier
    await loop.run_in_executor(None, get_classifier)
    print("Animal classifier pre-loaded.")
    
    # Start vaccination notification scheduler
    try:
        start_scheduler()
        print("Vaccination notification scheduler started.")
    except Exception as e:
        print(f"Failed to start vaccination scheduler: {e}")
    
    # Load new AI services
    try:
        from services.yolo_service import yolo_service
        from services.resnet_service import resnet_service
        from services.translation_service import translation_service
        
        # Initialize services (models will load on first access)
        print("AI/ML services initialized successfully.")
        print("- YOLOv8: Object detection ready")
        print("- ResNet50: Image classification ready") 
        print("- IndicTrans2: Translation service ready")
        print("- Location services ready")
        
    except Exception as e:
        print(f"Warning: Some AI services failed to initialize: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event to clean up resources.
    """
    print("Shutting down Jodettu API...")
    try:
        stop_scheduler()
        print("Vaccination notification scheduler stopped.")
    except Exception as e:
        print(f"Error stopping scheduler: {e}")
    print("Shutdown complete.")
    
    print("Server is ready to accept requests.")
