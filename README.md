# MEGA Web Downloader Pro

A modern, high-speed web application for downloading and streaming files from **MEGA.nz** directly to a local PC directory (e.g. `D:\anime`) or streaming straight to the browser.

---

## 🌟 Key Features

1. **Modern Cyberpunk/Dark Glassmorphism UI**:
   - Built with Tailwind CSS, Lucide icons, and responsive layouts.
   - Real-time progress bars, live transfer speed (MB/s), ETA countdown, and file sizes.

2. **Dual Download Engines**:
   - **Background Local Downloader**: Downloads in chunks with AES-CTR hardware decryption on-the-fly directly to your chosen PC folder (default: `D:\anime`).
   - **Direct Browser Streamer**: Streams decrypted file chunks straight to your browser's download manager.

3. **Link Inspector**:
   - Paste any MEGA link (`/file/...#...` or `/#!...!...`) and inspect file metadata (file name, size, type) before downloading.

4. **Task Management & Windows Explorer Integration**:
   - Pause or cancel active downloads with one click.
   - Click **Show in Folder** or **Open Folder** to launch Windows File Explorer highlighting the downloaded file.

5. **Folder File Explorer**:
   - Browse all existing downloaded files inside your target directory without leaving the web browser.

---

## 🚀 How to Run

### Method 1: One-Click Launcher (Recommended)
Simply double-click:
📂 **`D:\assessment\run.bat`**

It will start the local server and automatically launch your browser to:
👉 **`http://localhost:8000`**

### Method 2: Manual via Terminal
```powershell
cd D:\assessment
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
Open **`http://localhost:8000`** in your browser.

---

## 📁 Project Structure

```
D:\assessment\
├── app\
│   ├── __init__.py
│   ├── mega_engine.py       # MEGA API, crypto, and chunk decryption
│   └── task_manager.py      # Background worker, speed metrics, thread safety
├── static\
│   └── index.html           # Modern single-page web interface
├── main.py                  # FastAPI server and REST endpoints
├── requirements.txt         # Dependencies
├── run.bat                  # One-click Windows launcher
└── README.md
```
