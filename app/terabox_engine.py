import os
import re
import requests
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional

class TeraBoxEngine:
    SUPPORTED_DOMAINS = [
        "terabox.com",
        "1024tera.com",
        "1024terabox.com",
        "teraboxapp.com",
        "terabox.app",
        "freeterabox.com",
        "4funbox.com",
        "mirrobox.com",
        "nephobox.com",
        "momerybox.com",
        "tibibox.com"
    ]

    def is_terabox_url(self, url: str) -> bool:
        try:
            domain = urlparse(url).netloc.lower()
            return any(d in domain for d in self.SUPPORTED_DOMAINS)
        except Exception:
            return False

    def extract_surl(self, url: str) -> Optional[str]:
        # Examples: /s/1abcXYZ or /s/abcXYZ or ?surl=abcXYZ
        m = re.search(r'(?:/s/|surl=)([a-zA-Z0-9_-]+)', url)
        if m:
            surl = m.group(1)
            # TeraBox sometimes prefixes '1'
            return surl
        return None

    def get_file_info(self, url: str) -> Dict[str, Any]:
        """
        Attempts multiple methods to fetch file metadata from TeraBox link.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.terabox.com/"
        }

        surl = self.extract_surl(url)
        surl_no_1 = surl.lstrip('1') if surl else ""

        # Method 1: Public community bridge API for TeraBox
        api_endpoints = [
            f"https://terabox-dl.qtcloud.workers.dev/api/get-info?shorturl={surl}",
            f"https://terabox-dl.qtcloud.workers.dev/api/get-info?shorturl={surl_no_1}",
        ]

        for api_url in api_endpoints:
            try:
                res = requests.get(api_url, timeout=6)
                if res.status_code == 200:
                    data = res.json()
                    # Check if file list is present
                    list_files = data.get('list', []) or data.get('data', [])
                    if list_files and isinstance(list_files, list):
                        first = list_files[0]
                        file_name = first.get('server_filename') or first.get('filename') or 'terabox_file'
                        file_size = int(first.get('size', 0))
                        dlink = first.get('dlink') or first.get('download_url') or first.get('url')
                        return {
                            "file_name": file_name,
                            "file_size": file_size,
                            "file_extension": file_name.split('.')[-1].lower() if '.' in file_name else '',
                            "direct_url": dlink,
                            "provider": "terabox"
                        }
            except Exception:
                pass

        # Method 2: Fetch page directly and check for meta or video mp4/stream
        try:
            page = requests.get(url, headers=headers, timeout=8)
            title_m = re.search(r'<title>(.*?)</title>', page.text)
            page_title = title_m.group(1).split('-')[0].strip() if title_m else 'TeraBox Download'
            
            # Check for direct mp4 pattern
            mp4_m = re.search(r'"(https://[^"]+?\.mp4[^"]*)"', page.text)
            dlink = mp4_m.group(1) if mp4_m else None
            
            return {
                "file_name": f"{page_title}.mp4" if not page_title.endswith(('.mp4', '.zip', '.rar')) else page_title,
                "file_size": 0, # Will be determined on streaming
                "file_extension": "mp4",
                "direct_url": dlink or url,
                "provider": "terabox"
            }
        except Exception as e:
            raise ValueError(f"TeraBox Error: Could not resolve share link ({e})")
