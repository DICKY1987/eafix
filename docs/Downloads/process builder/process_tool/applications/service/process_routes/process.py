"""Process-related API routes for the service app."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/process")
def get_process():
    return {"process": "info"}
