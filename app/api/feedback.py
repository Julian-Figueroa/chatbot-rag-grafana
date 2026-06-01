from fastapi import APIRouter, HTTPException
from app.metrics import feedback_counter

router = APIRouter()

@router.post("/feedback")
async def feedback(session_id: str, rating: str): # up or down
  if rating not in ["up", "down"]:
    raise HTTPException(400, "rating must be 'up' or 'down'")
  
  # Increments Prometheus counter
  feedback_counter.labels(rating=rating).inc()

  # Optional: save on DB for future analysis
  return {"status": "recorded"}