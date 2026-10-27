import re
import gdown
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any

class GDriveEngine:
    def is_gdrive_url(self, url: str) -> bool:
        return "drive.google.com" in url or "docs.google.com" in url

    def extract_file_id(self, url: str) -> str:
        # e.g. /file/d/1abcXYZ/view or ?id=1abcXYZ
        m = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
        if m:
            return m.group(1)
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if 'id' in qs:
            return qs['id'][0]
        m2 = re.search(r'id=([a-zA-Z0-9_-]+)', url)
        if m2:
            return m2.group(1)
        raise ValueError("Could not extract Google Drive File ID from URL.")

    def get_file_info(self, url: str) -> Dict[str, Any]:
        file_id = self.extract_file_id(url)
        clean_url = f"https://drive.google.com/uc?id={file_id}"
        
        # Check metadata via gdown or requests
        try:
            # We can use gdown's internal helper to get filename if possible
            file_name = f"gdrive_{file_id}.zip"
            return {
                "file_name": file_name,
                "file_size": 0,
                "file_extension": "zip",
                "direct_url": clean_url,
                "provider": "gdrive",
                "file_id": file_id
            }
        except Exception as e:
            raise ValueError(f"Google Drive Error: {e}")

    def download_file(self, url: str, output_path: str):
        file_id = self.extract_file_id(url)
        clean_url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(clean_url, output=output_path, quiet=False, fuzzy=True)
