"""
API routes for the FastAPI service application.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def status():
    """Return the status of the service."""
    return {"status": "ok"}
