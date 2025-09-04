"""
FastAPI service application main entry point.
"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    """Root endpoint for the service API."""
    return {"message": "Service is running"}
