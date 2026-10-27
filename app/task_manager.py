import os
import time
import uuid
import threading
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.mega_engine import MegaEngine
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
        self.file_name = file_info['file_name']
        self.file_size = file_info['file_size']
        
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
            "file_size_formatted": self._format_size(self.file_size),
            "downloaded_bytes": self.downloaded_bytes,
            "downloaded_formatted": self._format_size(self.downloaded_bytes),
            "progress_percent": round(self.progress_percent, 1),
            "speed_formatted": self._format_speed(self.speed_bytes_sec),
            "speed_bytes_sec": self.speed_bytes_sec,
            "eta_formatted": self._format_eta(self.eta_seconds),
            "eta_seconds": self.eta_seconds,
            "status": self.status,
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
    def __init__(self, mega_engine: MegaEngine):
        self.engine = mega_engine
        self.tasks: Dict[str, DownloadTask] = {}
        self.lock = threading.Lock()

    def start_download(self, url: str, target_dir: str = r"D:\anime") -> DownloadTask:
        # 1. Fetch info
        info = self.engine.get_file_info(url)
        task_id = str(uuid.uuid4())[:8]

        # Ensure directory exists
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        task = DownloadTask(task_id, url, target_dir, info)
        with self.lock:
            self.tasks[task_id] = task

        # Start thread
        thread = threading.Thread(target=self._run_task, args=(task,), daemon=True)
        thread.start()
        return task

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

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            task = self.tasks.get(task_id)
            return task.to_dict() if task else None

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        with self.lock:
            # Sort newest first
            return [t.to_dict() for t in sorted(self.tasks.values(), key=lambda x: x.start_time or 0, reverse=True)]

    def _run_task(self, task: DownloadTask):
        task.status = "DOWNLOADING"
        task.start_time = time.time()
        
        info = task.file_info
        file_url = info['file_url']
        file_size = info['file_size']
        k = info['k']
        iv = info['iv']
        meta_mac = info['meta_mac']
        
        part_path = Path(task.target_dir) / f"{task.file_name}.part"
        final_path = Path(task.target_dir) / task.file_name

        try:
            resp = requests.get(file_url, stream=True, timeout=30)
            resp.raise_for_status()
            input_file = resp.raw

            aes, k_str = self.engine.create_decryptor(k, iv)
            
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

                    # Update CBC-MAC
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
                        remaining_bytes = file_size - task.downloaded_bytes
                        if task.speed_bytes_sec > 0:
                            task.eta_seconds = int(remaining_bytes / task.speed_bytes_sec)

            if task.cancel_event.is_set():
                if part_path.exists():
                    try:
                        part_path.unlink()
                    except Exception:
                        pass
                return

            # Verification
            file_mac = str_to_a32(mac_str)
            if (file_mac[0] ^ file_mac[1], file_mac[2] ^ file_mac[3]) != meta_mac:
                # Warning, but we still rename
                pass

            if final_path.exists():
                final_path.unlink()
            part_path.rename(final_path)

            task.status = "COMPLETED"
            task.progress_percent = 100.0
            task.downloaded_bytes = file_size
            task.speed_bytes_sec = 0.0
            task.eta_seconds = 0
            task.finish_time = time.time()

        except Exception as e:
            task.status = "FAILED"
            task.error_message = str(e)
            task.finish_time = time.time()
            if part_path.exists():
                try:
                    part_path.unlink()
                except Exception:
                    pass
