from typing import Dict, Any, Tuple
from app.mega_engine import MegaEngine
from app.terabox_engine import TeraBoxEngine
from app.gdrive_engine import GDriveEngine
from app.ytdlp_engine import YtDlpEngine
from app.direct_engine import DirectEngine

class UniversalEngine:
    def __init__(self):
        self.mega = MegaEngine()
        self.terabox = TeraBoxEngine()
        self.gdrive = GDriveEngine()
        self.ytdlp = YtDlpEngine()
        self.direct = DirectEngine()

    def detect_provider(self, url: str) -> str:
        url_lower = url.strip().lower()
        if "mega.nz" in url_lower:
            return "mega"
        if self.terabox.is_terabox_url(url_lower):
            return "terabox"
        if self.gdrive.is_gdrive_url(url_lower):
            return "gdrive"
        if self.ytdlp.is_media_url(url_lower):
            return "media"
        return "direct"

    def inspect_url(self, url: str) -> Dict[str, Any]:
        provider = self.detect_provider(url)
        
        if provider == "mega":
            info = self.mega.get_file_info(url)
            info["provider"] = "mega"
            return info
        elif provider == "terabox":
            info = self.terabox.get_file_info(url)
            return info
        elif provider == "gdrive":
            info = self.gdrive.get_file_info(url)
            return info
        elif provider == "media":
            info = self.ytdlp.get_file_info(url)
            return info
        else:
            info = self.direct.get_file_info(url)
            return info
