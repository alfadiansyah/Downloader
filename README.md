# OmniDownloader Pro - Universal Cloud & Media Downloader

A modern, high-speed universal web downloader supporting **MEGA.nz**, **TeraBox**, **Google Drive**, **YouTube / Social Media (yt-dlp)**, and **Direct HTTP/HTTPS** links. Files can be saved directly to any local directory on your PC (default: `D:\anime`) or streamed straight to your browser.

---

## 🌟 Key Features

1. **Universal Multi-Provider Support**:
   - **MEGA.nz**: High-speed chunk downloader with client-side AES-CTR decryption on-the-fly.
   - **TeraBox**: Direct extraction & download for `terabox.com`, `1024tera.com`, `teraboxapp.com`, and `freeterabox.com`.
   - **Google Drive**: Seamless download of public and large Drive files (with automated virus scan confirmation handling via `gdown`).
   - **Media & Social Video**: Supports YouTube, Twitter/X, TikTok, Instagram, and 1000+ media sites via `yt-dlp`.
   - **Direct HTTP/HTTPS**: High-speed chunked streaming for any direct file URL (ZIP, ISO, MP4, EXE, etc.) with custom headers and resume capabilities.

2. **Real-Time URL Provider Detection**:
   - As soon as you paste or type a URL, the interface automatically detects and highlights the provider badge (MEGA, TeraBox, GDrive, Media, Direct).

3. **Modern Dark Glassmorphism UI**:
   - Built with Tailwind CSS, Lucide icons, and responsive layouts.
   - Live metrics: speed (MB/s), downloaded bytes, ETA countdown, and animated progress bars.

4. **Background Task Manager & Explorer Integration**:
   - Multi-threaded background download engine with live polling.
   - Cancel downloads with one click.
   - Open downloaded files directly in Windows Explorer using the **Show** button.
   - Open the target directory with the **Open Folder** button.

5. **Folder File Manager**:
   - Browse, search, and inspect files already saved inside your target directory (e.g. `D:\anime`).

---

## 🚀 How to Run

### Method 1: One-Click Launcher (Recommended on Windows)
Simply double-click:
📂 **`D:\assessment\run.bat`**

It will start the server and automatically launch your browser to:
👉 **`http://localhost:8000`**

### Method 2: Manual via Terminal
```powershell
cd D:\assessment
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
Then open **`http://localhost:8000`** in your browser.

---

## 📁 Project Structure

```
D:\assessment\
├── app\
│   ├── __init__.py
│   ├── universal_engine.py   # Master dispatcher and link router
│   ├── mega_engine.py        # MEGA API & AES-CTR decryption engine
│   ├── terabox_engine.py     # TeraBox share link scraper & direct stream
│   ├── gdrive_engine.py      # Google Drive downloader (gdown)
│   ├── ytdlp_engine.py       # YouTube & media downloader (yt-dlp)
│   ├── direct_engine.py      # General HTTP/HTTPS chunked downloader
│   └── task_manager.py       # Thread pool, speed metrics, ETA, and state
├── static\
│   └── index.html            # Single-page web dashboard with auto-detection
├── main.py                   # FastAPI server and REST API endpoints
├── requirements.txt          # Python dependencies
├── run.bat                   # Windows one-click startup script
└── README.md
```

---

## 🔌 API Endpoints

- `GET /api/detect?url=...` - Auto-detect provider (`mega`, `terabox`, `gdrive`, `media`, `direct`)
- `POST /api/inspect` - Inspect URL metadata (filename, size, type, thumbnail)
- `POST /api/download` - Queue a background download to a local PC folder
- `GET /api/tasks` - List all active and past download tasks with real-time progress
- `POST /api/tasks/{id}/cancel` - Cancel an active download task
- `POST /api/tasks/{id}/open-folder` - Open the file's location in Windows Explorer
- `GET /api/stream?url=...` - Stream file directly to browser downloads
- `GET /api/history?target_dir=...` - List files in the target directory
