import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import os

from src.models.predictor import get_predictor
from src.database.models import DatabaseManager

#Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

#FastAPI app
app = FastAPI(
    title="EV Price Predictor API",
    description="Predict EV Prices",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

#CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Request/Response Models
class PredictionRequest(BaseModel):
    brand: str = Field(..., description="Car manufacturer", example="Tesla")
    model: str = Field(..., description="Car model", example="Model 3")
    battery: float = Field(..., ge=0, description="Battery capacity in kWh", example=75.0)
    autonomy: float = Field(..., ge=0, description="Range in km", example=500)
    safety: float = Field(..., ge=0, le=5, description="Safety rating (1-5)", example=4.0)
    year: int = Field(..., ge=2015, le=2026, description="Manufacturing year", example=2022)
    autonomous_level: Optional[float] = Field(0, ge=0, le=5, description="Autonomous driving level (0-5)", example=2.0)

class PredictionResponse(BaseModel):
    success: bool
    price: Optional[float] = None
    currency: str = "USD"
    metadata: Optional[dict] = None
    error: Optional[str] =None

class HistoryResponse(BaseModel):
    success: bool
    count: int
    predictions: List[dict]

#Initialize components
predictor = None
db = None
try:
    predictor = get_predictor()
    logger.info("Predictor initialized")
except Exception as e:
    logger.error(f"Predictor initialization failed: {e}")

try:
    db = DatabaseManager()
    logger.info("Database initialized")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

#Health Check
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "predictor": "loaded" if predictor else "failed",
        "database": "connected" if db else "disconnected"
    }

#Predict endpoint
@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest):
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Predictor not initialized"
        )

    try:
        try:
            #Convert request to dict
            input_data = request.model_dump()
        except AttributeError:
            input_data = request.dict()

        #Make predictiom
        price, metadata = predictor.predict(input_data)

        #Save to database
        if db:
            db.insert_prediction({
                'brand': request.brand,
                'model_name': request.model,
                'battery_capacity': request.battery,
                'range_km': request.autonomy,
                'safety_rating': request.safety,
                'year': request.year,
                'predicted_price': price
            })

        return PredictionResponse(
            success=True,
            price=price,
            currency="USD",
            metadata=metadata
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return PredictionResponse(success=False, error=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

#Batch prediction
@app.post("/predict/batch", tags=["Prediction"])
async def predict_batch(requests: List[PredictionRequest]):
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    results = []
    for req in requests:
        input_data = None
        try:
            try:
                input_data = req.model_dump()
            except AttributeError:
                input_data = req.dict()

            price, _ = predictor.predict(input_data)
            results.append({
                'input': input_data,
                'price': price,
                'success': True
            })
        except Exception as e:
            logger.warning(f"Batch prediction failed for one request: {e}")
            results.append({
                'input': input_data,
                'success': False,
                'error': str(e)
            })
    return {"results": results}

#History endpoint
@app.get("/history", response_model=HistoryResponse, tags=["History"])
async def get_history(limit: int = 100, offset: int = 0):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    predictions = db.get_history(limit=limit, offset=offset)
    return HistoryResponse(
        success=True,
        count=len(predictions),
        predictions=predictions
    )

#Stats endpoint
@app.get("/stats", tags=["System"])
async def get_stats():
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    return {"success": True, **db.get_stats()}