import os
import subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.universal_engine import UniversalEngine
from app.task_manager import TaskManager, DownloadTask

app = FastAPI(title="OmniDownloader Pro", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = UniversalEngine()
task_manager = TaskManager(engine)

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

class InspectRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    target_dir: str = r"D:\anime"

@app.get("/")
def get_index():
    return FileResponse(str(static_dir / "index.html"))

@app.get("/api/detect")
def detect_provider(url: str = Query(...)):
    provider = engine.detect_provider(url)
    return {"provider": provider}

@app.post("/api/inspect")
def inspect_url(req: InspectRequest):
    try:
        info = engine.inspect_url(req.url)
        size = info.get("file_size", 0)
        return {
            "success": True,
            "provider": info.get("provider", "direct"),
            "file_name": info["file_name"],
            "file_size": size,
            "file_size_formatted": DownloadTask._format_size(size) if size > 0 else "Dynamic / Stream",
            "file_extension": info.get("file_extension", ""),
            "thumbnail": info.get("thumbnail")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download")
def start_download(req: DownloadRequest):
    try:
        target_dir = req.target_dir.strip() if req.target_dir else r"D:\anime"
        task = task_manager.start_download(req.url, target_dir)
        return {"success": True, "task": task.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tasks")
def list_tasks():
    return {"tasks": task_manager.get_all_tasks()}

@app.post("/api/tasks/{task_id}/cancel")
def cancel_task(task_id: str):
    success = task_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or already completed/cancelled")
    return {"success": True, "task_id": task_id}

@app.post("/api/tasks/{task_id}/open-folder")
def open_folder(task_id: str):
    task = task_manager.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    path = Path(task.target_path)
    if path.exists():
        subprocess.run(f'explorer.exe /select,"{path}"', shell=True)
    elif Path(task.target_dir).exists():
        subprocess.run(f'explorer.exe "{task.target_dir}"', shell=True)
    else:
        raise HTTPException(status_code=400, detail="Target path or folder does not exist")
    return {"success": True}

@app.post("/api/open-directory")
def open_directory(dir_path: str = Query(r"D:\anime")):
    p = Path(dir_path)
    if p.exists():
        subprocess.run(f'explorer.exe "{p}"', shell=True)
        return {"success": True}
    raise HTTPException(status_code=404, detail="Directory not found")

@app.get("/api/stream")
def stream_download(url: str = Query(...)):
    """
    Directly streams file chunks to browser for native download!
    """
    provider = engine.detect_provider(url)
    try:
        info = engine.inspect_url(url)
        if provider == "mega":
            headers = {
                "Content-Disposition": f'attachment; filename="{info["file_name"]}"',
                "Content-Length": str(info["file_size"]),
                "Content-Type": "application/octet-stream"
            }
            return StreamingResponse(engine.mega.stream_decrypted_chunks(info), headers=headers)
        else:
            direct_url = info.get("direct_url") or url
            import requests
            def stream_gen():
                with requests.get(direct_url, stream=True) as r:
                    for chunk in r.iter_content(chunk_size=128 * 1024):
                        if chunk:
                            yield chunk
            headers = {
                "Content-Disposition": f'attachment; filename="{info["file_name"]}"',
                "Content-Type": "application/octet-stream"
            }
            if info.get("file_size"):
                headers["Content-Length"] = str(info["file_size"])
            return StreamingResponse(stream_gen(), headers=headers)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/history")
def get_folder_files(target_dir: str = Query(r"D:\anime")):
    p = Path(target_dir)
    if not p.exists():
        return {"files": []}
    
    files = []
    for f in p.iterdir():
        if f.is_file() and not f.name.endswith(".part"):
            st = f.stat()
            files.append({
                "name": f.name,
                "size": st.st_size,
                "size_formatted": DownloadTask._format_size(st.st_size),
                "modified": st.st_mtime,
                "path": str(f)
            })
    files.sort(key=lambda x: x["modified"], reverse=True)
    return {"files": files}
