# OmniDownloader Pro - Workstation Web Downloader

A high-performance universal web downloader and queue workstation supporting **MEGA.nz**, **TeraBox**, **Google Drive**, **YouTube / Social Media (yt-dlp)**, and **Direct HTTP/HTTPS** links. Files can be saved directly to any local directory on your PC (default: `D:\anime`) or streamed straight to your browser.

---

## 🌟 Key Features

1. **Universal Multi-Provider Support**:
   - **MEGA.nz**: High-speed chunk downloader with client-side AES-CTR decryption on-the-fly.
   - **TeraBox**: Direct extraction & download for `terabox.com`, `1024tera.com`, `teraboxapp.com`, and `freeterabox.com`.
   - **Google Drive**: Seamless download of public and large Drive files (with automated virus scan confirmation handling via `gdown`).
   - **Media & Social Video**: Supports YouTube, Twitter/X, TikTok, Instagram, and 1000+ media sites via `yt-dlp`.
   - **Direct HTTP/HTTPS**: High-speed chunked streaming for any direct file URL (ZIP, ISO, MP4, EXE, etc.) with custom headers and resume capabilities.

2. **Batch Downloader & Queue Manager**:
   - Paste dozens of URLs simultaneously (one per line) in **Batch Mode**.
   - Automated concurrency semaphore (max 3 active concurrent downloads, remainder queued for slot release).
   - Real-time batch URL parser with blank line and `#` comment filtering.

3. **Minimalist Pro Utility UI (Anti-Slop Crafting)**:
   - High information density inspired by professional desktop clients (qBittorrent, Transmission).
   - Monospace tabular numeric columns for speed, percentage, ETA, and byte counters.
   - Live aggregate bandwidth meter (`Total Speed: X.X MB/s`).
   - Global queue controls: **Clear Finished**, **Cancel All**, **Retry Task**, **Show in Explorer**.

4. **Background Task Engine & Windows Explorer Integration**:
   - Multi-threaded background download engine with live polling.
   - Open downloaded files directly in Windows Explorer using the **Show** button.
   - Open target destination directly with the **Explorer** button.

5. **Folder File Manager**:
   - Browse, locate, and inspect files already saved inside your target directory (e.g. `D:\anime`).

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
│   └── task_manager.py       # Concurrency queue (semaphore), speed metrics, ETA
├── static\
│   └── index.html            # Minimalist Pro single-page web dashboard
├── main.py                   # FastAPI server and REST API endpoints
├── DESIGN.md                 # Antislop style direction & dials
├── AGENTS.md                 # Antislop agent pointer configuration
├── requirements.txt          # Python dependencies
├── run.bat                   # Windows one-click startup script
└── README.md
```

---

## 🔌 API Endpoints

- `GET /api/detect?url=...` - Auto-detect provider (`mega`, `terabox`, `gdrive`, `media`, `direct`)
- `POST /api/inspect` - Inspect URL metadata (filename, size, type)
- `POST /api/download` - Queue a single download
- `POST /api/batch-download` - Queue multiple download links in one batch
- `GET /api/tasks` - List all active/queued tasks with aggregate queue stats
- `POST /api/tasks/{id}/cancel` - Cancel an active download task
- `POST /api/tasks/{id}/retry` - Retry a failed or cancelled task
- `POST /api/tasks/clear-finished` - Clean up completed/failed tasks from the list
- `POST /api/tasks/cancel-all` - Stop all active and queued tasks
- `POST /api/tasks/{id}/open-folder` - Open the file's location in Windows Explorer
- `GET /api/stream?url=...` - Stream file directly to browser downloads
- `GET /api/history?target_dir=...` - List files in the target directory
