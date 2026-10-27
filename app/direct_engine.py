import os
import re
import requests
from urllib.parse import urlparse, unquote
from typing import Dict, Any, Optional

class DirectEngine:
    def get_file_info(self, url: str) -> Dict[str, Any]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            # Send HEAD or Range GET request
            res = requests.head(url, headers=headers, allow_redirects=True, timeout=8)
            if res.status_code >= 400:
                # Some servers reject HEAD, try GET with stream=True
                res = requests.get(url, headers=headers, stream=True, allow_redirects=True, timeout=8)
            
            # Content-Disposition filename
            file_name = None
            cd = res.headers.get("content-disposition", "")
            if cd:
                m = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';\r\n]+)', cd, re.IGNORECASE)
                if m:
                    file_name = unquote(m.group(1).strip())
            
            if not file_name:
                path = urlparse(res.url).path
                file_name = unquote(os.path.basename(path)) if path else ""
            
            if not file_name or len(file_name) < 2 or '.' not in file_name:
                file_name = "download_file.bin"

            content_length = int(res.headers.get("content-length", 0))
            ext = file_name.split('.')[-1].lower() if '.' in file_name else ''

            return {
                "file_name": file_name,
                "file_size": content_length,
                "file_extension": ext,
                "direct_url": res.url,
                "provider": "direct"
            }
        except Exception as e:
            raise ValueError(f"Direct URL Error: {e}")
