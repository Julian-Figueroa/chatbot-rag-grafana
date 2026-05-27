from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
import os

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def verify_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.getenv("API_KEY", "change-me-in-production")
    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")