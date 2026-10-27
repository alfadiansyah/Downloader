import os
import yt_dlp
from typing import Dict, Any, Callable, Optional

class YtDlpEngine:
    MEDIA_DOMAINS = [
        "youtube.com",
        "youtu.be",
        "tiktok.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "facebook.com",
        "fb.watch",
        "vimeo.com",
        "reddit.com",
        "twitch.tv",
        "dailymotion.com",
        "bilibili.com"
    ]

    def is_media_url(self, url: str) -> bool:
        url_lower = url.lower()
        return any(d in url_lower for d in self.MEDIA_DOMAINS)

    def get_file_info(self, url: str) -> Dict[str, Any]:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'media_video')
                ext = info.get('ext', 'mp4')
                filesize = info.get('filesize') or info.get('filesize_approx') or 0
                return {
                    "file_name": f"{title}.{ext}",
                    "file_size": filesize,
                    "file_extension": ext,
                    "thumbnail": info.get('thumbnail'),
                    "duration": info.get('duration'),
                    "provider": "media",
                    "url": url
                }
            except Exception as e:
                raise ValueError(f"Media Resolver Error: {e}")

    def download(self, url: str, target_dir: str, progress_hook: Optional[Callable] = None):
        out_tmpl = os.path.join(target_dir, '%(title)s.%(ext)s')
        ydl_opts = {
            'outtmpl': out_tmpl,
            'format': 'bestvideo+bestaudio/best',
            'no_warnings': True,
            'quiet': True,
        }
        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
