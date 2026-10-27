import os
import time
import uuid
import threading
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.universal_engine import UniversalEngine
from mega.crypto import (
    a32_to_str,
    str_to_a32,
    get_chunks,
    AES,
)

class DownloadTask:
    def __init__(self, task_id: str, url: str, target_dir: str, file_info: Dict[str, Any]):
        self.task_id = task_id
        self.url = url
        self.target_dir = target_dir
        self.file_info = file_info
        self.file_name = file_info.get('file_name', 'downloaded_file')
        self.file_size = file_info.get('file_size', 0)
        self.provider = file_info.get('provider', 'direct')
        
        self.downloaded_bytes = 0
        self.progress_percent = 0.0
        self.speed_bytes_sec = 0.0
        self.eta_seconds = 0
        
        self.status = "QUEUED"  # QUEUED, DOWNLOADING, COMPLETED, FAILED, CANCELLED
        self.error_message: Optional[str] = None
        self.target_path = str(Path(target_dir) / self.file_name)
        
        self.start_time: Optional[float] = None
        self.finish_time: Optional[float] = None
        self.cancel_event = threading.Event()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "url": self.url,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_size_formatted": self._format_size(self.file_size) if self.file_size > 0 else "Dynamic / Stream",
            "downloaded_bytes": self.downloaded_bytes,
            "downloaded_formatted": self._format_size(self.downloaded_bytes),
            "progress_percent": round(self.progress_percent, 1),
            "speed_formatted": self._format_speed(self.speed_bytes_sec),
            "speed_bytes_sec": self.speed_bytes_sec,
            "eta_formatted": self._format_eta(self.eta_seconds),
            "eta_seconds": self.eta_seconds,
            "status": self.status,
            "provider": self.provider,
            "error_message": self.error_message,
            "target_dir": self.target_dir,
            "target_path": self.target_path,
            "elapsed_seconds": int(time.time() - self.start_time) if self.start_time and not self.finish_time else (int(self.finish_time - self.start_time) if self.start_time and self.finish_time else 0)
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.2f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.2f} GB"

    @staticmethod
    def _format_speed(bytes_per_sec: float) -> str:
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.1f} B/s"
        elif bytes_per_sec < 1024 ** 2:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_sec / (1024 ** 2):.2f} MB/s"

    @staticmethod
    def _format_eta(seconds: int) -> str:
        if seconds <= 0:
            return "--"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}h {m}m {s}s"
        elif m > 0:
            return f"{m}m {s}s"
        else:
            return f"{s}s"


class TaskManager:
    def __init__(self, universal_engine: UniversalEngine, max_concurrent: int = 3):
        self.engine = universal_engine
        self.tasks: Dict[str, DownloadTask] = {}
        self.lock = threading.Lock()
        self.max_concurrent = max_concurrent
        self.semaphore = threading.Semaphore(self.max_concurrent)

    def start_download(self, url: str, target_dir: str = r"D:\anime") -> DownloadTask:
        info = self.engine.inspect_url(url)
        task_id = str(uuid.uuid4())[:8]

        Path(target_dir).mkdir(parents=True, exist_ok=True)

        task = DownloadTask(task_id, url, target_dir, info)
        with self.lock:
            self.tasks[task_id] = task

        thread = threading.Thread(target=self._task_worker, args=(task,), daemon=True)
        thread.start()
        return task

    def batch_start_downloads(self, urls: List[str], target_dir: str = r"D:\anime") -> Dict[str, Any]:
        created_tasks = []
        errors = []
        for raw_url in urls:
            u = raw_url.strip()
            if not u or u.startswith("#"):
                continue
            try:
                task = self.start_download(u, target_dir)
                created_tasks.append(task.to_dict())
            except Exception as e:
                errors.append({"url": u, "error": str(e)})
        return {"tasks": created_tasks, "errors": errors}

    def cancel_task(self, task_id: str) -> bool:
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            if task.status in ["QUEUED", "DOWNLOADING"]:
                task.cancel_event.set()
                task.status = "CANCELLED"
                task.finish_time = time.time()
                return True
            return False

    def cancel_all_active(self) -> int:
        count = 0
        with self.lock:
            for task in self.tasks.values():
                if task.status in ["QUEUED", "DOWNLOADING"]:
                    task.cancel_event.set()
                    task.status = "CANCELLED"
                    task.finish_time = time.time()
                    count += 1
        return count

    def retry_task(self, task_id: str) -> Optional[DownloadTask]:
        with self.lock:
            task = self.tasks.get(task_id)
            if not task or task.status not in ["FAILED", "CANCELLED"]:
                return None
            task.cancel_event.clear()
            task.status = "QUEUED"
            task.downloaded_bytes = 0
            task.progress_percent = 0.0
            task.speed_bytes_sec = 0.0
            task.eta_seconds = 0
            task.error_message = None
            task.start_time = None
            task.finish_time = None

        thread = threading.Thread(target=self._task_worker, args=(task,), daemon=True)
        thread.start()
        return task

    def clear_finished(self) -> int:
        with self.lock:
            to_delete = [
                tid for tid, t in self.tasks.items()
                if t.status in ["COMPLETED", "FAILED", "CANCELLED"]
            ]
            for tid in to_delete:
                del self.tasks[tid]
            return len(to_delete)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            task = self.tasks.get(task_id)
            return task.to_dict() if task else None

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [t.to_dict() for t in sorted(self.tasks.values(), key=lambda x: x.start_time or 0, reverse=True)]

    def get_aggregate_stats(self) -> Dict[str, Any]:
        with self.lock:
            tasks = list(self.tasks.values())
        active = sum(1 for t in tasks if t.status == "DOWNLOADING")
        queued = sum(1 for t in tasks if t.status == "QUEUED")
        completed = sum(1 for t in tasks if t.status == "COMPLETED")
        failed = sum(1 for t in tasks if t.status == "FAILED")
        speed = sum(t.speed_bytes_sec for t in tasks if t.status == "DOWNLOADING")
        return {
            "active_count": active,
            "queued_count": queued,
            "completed_count": completed,
            "failed_count": failed,
            "total_count": len(tasks),
            "total_speed_bytes": speed,
            "total_speed_formatted": DownloadTask._format_speed(speed),
            "max_concurrent": self.max_concurrent
        }

    def _task_worker(self, task: DownloadTask):
        if task.cancel_event.is_set():
            task.status = "CANCELLED"
            task.finish_time = time.time()
            return

        with self.semaphore:
            if task.cancel_event.is_set():
                task.status = "CANCELLED"
                task.finish_time = time.time()
                return
            self._run_task(task)

    def _run_task(self, task: DownloadTask):
        task.status = "DOWNLOADING"
        task.start_time = time.time()
        provider = task.provider

        try:
            if provider == "mega":
                self._download_mega(task)
            elif provider == "media":
                self._download_media(task)
            elif provider == "gdrive":
                self._download_gdrive(task)
            else:
                self._download_stream(task)
                
            if task.status == "DOWNLOADING":
                task.status = "COMPLETED"
                task.progress_percent = 100.0
                task.speed_bytes_sec = 0.0
                task.eta_seconds = 0
                task.finish_time = time.time()

        except Exception as e:
            if not task.cancel_event.is_set():
                task.status = "FAILED"
                task.error_message = str(e)
            else:
                task.status = "CANCELLED"
            task.finish_time = time.time()

    def _download_mega(self, task: DownloadTask):
        info = task.file_info
        file_url = info['file_url']
        file_size = info['file_size']
        k = info['k']
        iv = info['iv']
        meta_mac = info['meta_mac']
        
        part_path = Path(task.target_dir) / f"{task.file_name}.part"
        final_path = Path(task.target_dir) / task.file_name

        resp = requests.get(file_url, stream=True, timeout=30)
        resp.raise_for_status()
        input_file = resp.raw

        aes, k_str = self.engine.mega.create_decryptor(k, iv)
        mac_str = '\0' * 16
        mac_encryptor = AES.new(k_str, AES.MODE_CBC, mac_str.encode("utf8"))
        iv_str = a32_to_str([iv[0], iv[1], iv[0], iv[1]])

        speed_timer = time.time()
        bytes_since_timer = 0

        with open(part_path, 'wb') as f_out:
            for _, chunk_size in get_chunks(file_size):
                if task.cancel_event.is_set():
                    task.status = "CANCELLED"
                    break

                chunk = input_file.read(chunk_size)
                if not chunk:
                    break

                dec_chunk = aes.decrypt(chunk)
                f_out.write(dec_chunk)

                encryptor = AES.new(k_str, AES.MODE_CBC, iv_str)
                for i in range(0, len(dec_chunk) - 16, 16):
                    encryptor.encrypt(dec_chunk[i:i + 16])
                i = (i + 16) if file_size > 16 else 0
                block = dec_chunk[i:i + 16]
                if len(block) % 16:
                    block += b'\0' * (16 - (len(block) % 16))
                mac_str = mac_encryptor.encrypt(encryptor.encrypt(block))

                chunk_len = len(dec_chunk)
                task.downloaded_bytes += chunk_len
                bytes_since_timer += chunk_len
                task.progress_percent = (task.downloaded_bytes / file_size) * 100 if file_size > 0 else 0

                now = time.time()
                elapsed_interval = now - speed_timer
                if elapsed_interval >= 1.0:
                    task.speed_bytes_sec = bytes_since_timer / elapsed_interval
                    speed_timer = now
                    bytes_since_timer = 0
                    if task.speed_bytes_sec > 0:
                        task.eta_seconds = int((file_size - task.downloaded_bytes) / task.speed_bytes_sec)

        if task.cancel_event.is_set():
            if part_path.exists():
                try: part_path.unlink()
                except Exception: pass
            return

        file_mac = str_to_a32(mac_str)
        if final_path.exists():
            final_path.unlink()
        part_path.rename(final_path)

    def _download_stream(self, task: DownloadTask):
        url = task.file_info.get('direct_url') or task.url
        part_path = Path(task.target_dir) / f"{task.file_name}.part"
        final_path = Path(task.target_dir) / task.file_name

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, stream=True, timeout=30)
        resp.raise_for_status()

        total = int(resp.headers.get('content-length', 0))
        if total > 0 and task.file_size == 0:
            task.file_size = total

        speed_timer = time.time()
        bytes_since_timer = 0

        with open(part_path, 'wb') as f_out:
            for chunk in resp.iter_content(chunk_size=128 * 1024):
                if task.cancel_event.is_set():
                    task.status = "CANCELLED"
                    break
                if not chunk:
                    continue
                f_out.write(chunk)
                chunk_len = len(chunk)
                task.downloaded_bytes += chunk_len
                bytes_since_timer += chunk_len

                if task.file_size > 0:
                    task.progress_percent = (task.downloaded_bytes / task.file_size) * 100

                now = time.time()
                elapsed = now - speed_timer
                if elapsed >= 1.0:
                    task.speed_bytes_sec = bytes_since_timer / elapsed
                    speed_timer = now
                    bytes_since_timer = 0
                    if task.speed_bytes_sec > 0 and task.file_size > task.downloaded_bytes:
                        task.eta_seconds = int((task.file_size - task.downloaded_bytes) / task.speed_bytes_sec)

        if task.cancel_event.is_set():
            if part_path.exists():
                try: part_path.unlink()
                except Exception: pass
            return

        if final_path.exists():
            final_path.unlink()
        part_path.rename(final_path)

    def _download_media(self, task: DownloadTask):
        def hook(d):
            if task.cancel_event.is_set():
                raise KeyboardInterrupt("Cancelled")
            if d['status'] == 'downloading':
                task.downloaded_bytes = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                if total > 0:
                    task.file_size = total
                    task.progress_percent = (task.downloaded_bytes / total) * 100
                task.speed_bytes_sec = d.get('speed', 0) or 0
                task.eta_seconds = d.get('eta', 0) or 0

        self.engine.ytdlp.download(task.url, task.target_dir, progress_hook=hook)

    def _download_gdrive(self, task: DownloadTask):
        final_path = Path(task.target_dir) / task.file_name
        self.engine.gdrive.download_file(task.url, str(final_path))
        if final_path.exists():
            task.downloaded_bytes = final_path.stat().st_size
            task.file_size = task.downloaded_bytes
            task.progress_percent = 100.0
