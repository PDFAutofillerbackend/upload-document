# app/routes/upload.py
from fastapi import APIRouter, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import json
import subprocess
from typing import List
from backend import code7

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent.parent
SAMPLES_DIR = BASE_DIR / "samples"
BACKEND_DIR = BASE_DIR / "backend"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/sessions/create")
async def create_session(session_name: str = Form(...)):
    session_path = SAMPLES_DIR / session_name
    if session_path.exists():
        raise HTTPException(status_code=400, detail="Session already exists")
    session_path.mkdir(parents=True)
    return {"detail": f"Session '{session_name}' created successfully"}


@router.get("/sessions")
async def list_sessions():
    sessions = []
    for session_folder in SAMPLES_DIR.iterdir():
        if session_folder.is_dir():
            doc_count = len(list(session_folder.glob("*")))
            sessions.append({"session_name": session_folder.name, "document_count": doc_count})
    return {"sessions": sessions}


@router.get("/sessions/{session_name}")
async def get_session(session_name: str):
    session_path = SAMPLES_DIR / session_name
    if not session_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    documents = []
    for file in session_path.iterdir():
        if file.is_dir():
            final_file = file / "final_output_form_keys_filled.json"
            status = "completed" if final_file.exists() else "pending"
            documents.append({"document_name": file.name, "status": status})

    total_docs = len(documents)
    processed_docs = sum(1 for d in documents if d["status"] == "completed")

    return {"total_documents": total_docs, "processed_documents": processed_docs, "documents": documents}


@router.post("/sessions/{session_name}/upload")
async def upload_files(session_name: str, files: List[UploadFile]):
    session_path = SAMPLES_DIR / session_name
    if not session_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    uploaded_files = []
    for file in files:
        doc_name = Path(file.filename).stem
        doc_folder = session_path / doc_name
        doc_folder.mkdir(parents=True, exist_ok=True)

        dest = doc_folder / file.filename
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        uploaded_files.append(f"{doc_name}/{file.filename}")

    return {"files": uploaded_files}


@router.post("/sessions/{session_name}/process")
async def process_session(session_name: str):
    session_path = SAMPLES_DIR / session_name
    if not session_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    results = []
    succeeded = 0
    total = 0

    doc_folders = sorted([d for d in session_path.iterdir() if d.is_dir()])
    if not doc_folders:
        return {"results": [], "succeeded": 0, "total": 0}

    session_json_path = session_path / f"final_{session_name}_form_keys_filled.json"
    first_doc = not session_json_path.exists()

    for doc_folder in doc_folders:
        final_output = doc_folder / "final_output_form_keys_filled.json"
        if final_output.exists():
            results.append({"document": doc_folder.name, "status": "skipped", "message": "Already processed"})
            continue

        input_file = next(
            (f for f in doc_folder.iterdir() if f.is_file() and f.suffix.lower() in [".pdf", ".docx", ".xlsx", ".csv", ".json", ".txt"]),
            None
        )
        if not input_file:
            results.append({"document": doc_folder.name, "status": "failed", "error": "No valid file found"})
            continue

        total += 1

        try:
            # Run code1 → code2
            subprocess.run(["python", str(BACKEND_DIR / "code1.py"), str(input_file), str(doc_folder)], check=True)
            subprocess.run(["python", str(BACKEND_DIR / "code2.py"), str(doc_folder)], check=True)

            if first_doc:
                # First document: run code5 → code6
                subprocess.run(["python", str(BACKEND_DIR / "code5.py"), str(doc_folder)], check=True)
                subprocess.run(["python", str(BACKEND_DIR / "code6.py"), str(doc_folder)], check=True)

                # Copy code6 output → final_output_form_keys_filled.json
                shutil.copy(doc_folder / "code6_output_form_keys_filled.json", final_output)
                first_doc = False
            else:
                # Subsequent PDFs: copy code2 output → final_output_form_keys_filled.json
                shutil.copy(doc_folder / "code2_output.json", final_output)

            # Merge into session-level JSON using code7
            code7.merge_pdf_into_session(str(doc_folder), str(session_json_path))

            results.append({"document": input_file.name, "status": "success", "message": "Processed successfully"})
            succeeded += 1

        except subprocess.CalledProcessError as e:
            results.append({"document": input_file.name, "status": "failed", "error": str(e)})
        except Exception as e:
            results.append({"document": input_file.name, "status": "failed", "error": f"Merge failed: {e}"})

    return {"results": results, "succeeded": succeeded, "total": total}


@router.post("/sessions/{session_name}/aggregate")
async def aggregate_session(session_name: str):
    session_path = SAMPLES_DIR / session_name
    if not session_path.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    aggregated = {}
    for file in session_path.glob("*/final_output_form_keys_filled.json"):
        with open(file, "r", encoding="utf-8") as f:
            aggregated[file.parent.name] = json.load(f)

    agg_file = session_path / "aggregated_session_output.json"
    with open(agg_file, "w", encoding="utf-8") as f:
        json.dump(aggregated, f, indent=4, ensure_ascii=False)

    return {"detail": f"Aggregated output saved to {agg_file.name}"}


@router.get("/sessions/{session_name}/download")
async def download_session_output(session_name: str):
    session_path = SAMPLES_DIR / session_name
    agg_file = session_path / "aggregated_session_output.json"
    if not agg_file.exists():
        raise HTTPException(status_code=404, detail="Aggregated output not found. Please aggregate first.")
    return FileResponse(agg_file, media_type="application/json", filename=agg_file.name)