from fastapi import FastAPI, File, UploadFile, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import os

from .models.model_manager import AnimalRecognitionModel
from .routes.animal_classification import router as animal_router
from routes.login_routes import router as login_router
from routes.animal_routes import router as animal_management_router
from routes.feed_medicine_routes import router as feed_medicine_router
from routes.machine_routes import router as machine_router
from routes.ai_routes import router as ai_router
from routes.enhanced_ai_routes import router as enhanced_ai_router
from routes.notification_routes import router as notification_router
from routes.product_routes import router as product_router
from routes.wishlist_routes import router as wishlist_router
from .utils.schemas import AnimalRecognitionResponse, ErrorResponse
from .config import settings

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for animal recognition including breed and disease detection",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Animal Recognition",
            "description": "Endpoints for animal image analysis"
        },
        {
            "name": "Animal Classification",
            "description": "Endpoints for animal and breed classification"
        },
        {
            "name": "Authentication",
            "description": "Endpoints for user authentication and registration"
        },
        {
            "name": "Animal Management",
            "description": "Endpoints for animal CRUD operations"
        },
        {
            "name": "Feed & Medicine",
            "description": "Endpoints for feed and medicine management"
        },
        {
            "name": "Machine Management",
            "description": "Endpoints for machine operations"
        },
        {
            "name": "Health",
            "description": "Health check endpoints"
        },
        {
            "name": "AI Services",
            "description": "AI/ML endpoints including detection and classification"
        },
        {
            "name": "Enhanced AI",
            "description": "Enhanced AI endpoints for detailed analysis and training data"
        },
        {
            "name": "Notifications",
            "description": "Notification management endpoints"
        },
        {
            "name": "Wishlist",
            "description": "Wishlist management endpoints"
        },
        {
            "name": "Products",
            "description": "Product wishlist endpoints"
        }
    ]
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(animal_router)
app.include_router(login_router, tags=["Authentication"])
app.include_router(animal_management_router, tags=["Animal Management"])
app.include_router(feed_medicine_router, tags=["Feed & Medicine"])
app.include_router(machine_router, tags=["Machine Management"])
app.include_router(ai_router, tags=["AI Services"])
app.include_router(enhanced_ai_router, tags=["Enhanced AI"])
app.include_router(notification_router, tags=["Notifications"])
app.include_router(product_router, tags=["Products"])
app.include_router(wishlist_router, prefix="/wishlist", tags=["Wishlist"])

# Lazy model loading - will be initialized on first request
model = None

def get_model():
    """Thread-safe singleton getter for the model"""
    global model
    if model is None:
        from .models.model_manager import AnimalRecognitionModel
        model = AnimalRecognitionModel()
    return model

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Animal Recognition API is running"}

# Animal recognition endpoint
@app.post(
    "/analyze",
    response_model=AnimalRecognitionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["Animal Recognition"]
)
async def analyze_animal_image(
    file: UploadFile = File(..., description="Image file to analyze")
):
    """
    Analyze an animal image and return predictions for:
    - Animal type
    - Breed
    - Visible skin disease
    """
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Validate file size
    file.file.seek(0, 2)  # Go to end of file
    file_size = file.file.tell()
    file.file.seek(0)  # Reset file pointer
    
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size is {settings.MAX_FILE_SIZE // (1024 * 1024)}MB"
        )
    
    try:
        # Get model using lazy loading
        model_instance = get_model()
        # Get predictions
        predictions = await model_instance.predict(file)
        return predictions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )

# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services when the app starts"""
    # Any initialization code can go here
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
