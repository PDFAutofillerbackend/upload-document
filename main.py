# main.py
import os
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
from typing import List

# Backend pipeline
from backend import run_pipeline

# ==================== App Setup ====================
app = FastAPI(title="Document Processing Pipeline", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend (optional)
from fastapi.responses import FileResponse
app.mount("/static", Path("frontend/static"), name="static")

# ==================== Config ====================
SAMPLES_DIR = Path("samples")
SAMPLES_DIR.mkdir(exist_ok=True)

# ==================== Helpers ====================
def get_session_path(session_name: str) -> Path:
    return SAMPLES_DIR / session_name

# ==================== API Endpoints ====================
@app.post("/api/sessions/create")
async def create_session(session_name: str = Form(...)):
    session_name = session_name.strip()
    if not session_name:
        raise HTTPException(status_code=400, detail="Session name cannot be empty")
    session_path = get_session_path(session_name)
    if session_path.exists():
        raise HTTPException(status_code=400, detail="Session already exists")
    session_path.mkdir(parents=True, exist_ok=True)
    return {"message": "Session created successfully", "session_name": session_name}

@app.get("/api/sessions")
async def list_sessions():
    sessions = []
    for session_dir in SAMPLES_DIR.iterdir():
        if session_dir.is_dir():
            docs = [d.name for d in session_dir.iterdir() if d.is_dir()]
            processed_count = sum(1 for d in session_dir.iterdir() if d.is_dir() and (d / f"processed_{d.name}.json").exists())
            sessions.append({
                "session_name": session_dir.name,
                "document_count": len(docs),
                "processed_documents": processed_count,
                "documents": [{"document_name": d, "status": "processed" if (session_dir / d / f"processed_{d}.json").exists() else "pending"} for d in docs]
            })
    return {"sessions": sessions}

@app.get("/api/sessions/{session_name}")
async def get_session_details(session_name: str):
    session_path = get_session_path(session_name)
    if not session_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    docs = [d.name for d in session_path.iterdir() if d.is_dir()]
    processed_count = sum(1 for d in session_path.iterdir() if d.is_dir() and (d / f"processed_{d.name}.json").exists())
    return {
        "session_name": session_name,
        "total_documents": len(docs),
        "processed_documents": processed_count,
        "documents": [{"document_name": d, "status": "processed" if (session_path / d / f"processed_{d}.json").exists() else "pending"} for d in docs]
    }

@app.post("/api/sessions/{session_name}/upload_process")
async def upload_and_process_documents(session_name: str, files: List[UploadFile] = File(...), override: bool = Form(False)):
    """
    Upload files and run the full pipeline automatically.
    """
    session_path = get_session_path(session_name)
    if not session_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    session_json = session_path / f"final_{session_name}_form_keys_filled.json"
    results = []

    for file in files:
        allowed_extensions = {'.pdf', '.csv', '.xlsx', '.docx', '.json'}
        ext = Path(file.filename).suffix.lower()
        if ext not in allowed_extensions:
            results.append({"filename": file.filename, "status": "skipped", "reason": "Unsupported file type"})
            continue

        # Create folder for document
        doc_name = Path(file.filename).stem
        doc_folder = session_path / doc_name
        doc_folder.mkdir(parents=True, exist_ok=True)

        # Save uploaded file
        file_path = doc_folder / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run full pipeline
        try:
            session_json_path = run_pipeline.run_full_pipeline(
                str(file_path), str(doc_folder), str(session_json), override
            )
            results.append({"document": doc_name, "status": "success"})
        except Exception as e:
            results.append({"document": doc_name, "status": "failed", "error": str(e)})

    return {"session": session_name, "results": results}

@app.delete("/api/sessions/{session_name}")
async def delete_session(session_name: str):
    session_path = get_session_path(session_name)
    if not session_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    shutil.rmtree(session_path)
    return {"message": "Session deleted successfully"}

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")