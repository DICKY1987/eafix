from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/validate")
async def validate(file: UploadFile = File(...)):
    # Stub: echo back filename
    return {"diagnostics": [{"severity": "INFO", "code": "APF0000", "message": f"validated {file.filename}"}]}

@router.post("/export")
async def export(file: UploadFile = File(...), format: str = "md"):
    # Stub: echo back request
    return {"artifact": f"{file.filename}.{format}", "note": "stubbed export"}

@router.post("/decide")
async def decide(payload: dict):
    # Stub: echo back
    return JSONResponse({"decision": "stub", "input": payload})