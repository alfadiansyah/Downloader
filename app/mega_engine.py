import re
import requests
from typing import Dict, Any, Generator, Tuple
from Crypto.Cipher import AES
from Crypto.Util import Counter

from mega import Mega
from mega.crypto import (
    base64_to_a32,
    base64_url_decode,
    decrypt_attr,
    a32_to_str,
    str_to_a32,
    get_chunks,
)

class MegaEngine:
    def __init__(self):
        self._mega = Mega()
        self._client = self._mega.login()

    def parse_url(self, url: str) -> Tuple[str, str]:
        """
        Parses MEGA file url into (file_handle, file_key).
        Supports:
          - https://mega.nz/file/<id>#<key>
          - https://mega.nz/#!<id>!<key>
        """
        url = url.strip()
        if '/file/' in url:
            # V2 URL structure: /file/<id>#<key>
            parts = url.split('/file/')[1].split('#')
            if len(parts) >= 2:
                file_id = parts[0].strip()
                file_key = parts[1].strip()
                return file_id, file_key
        elif '#!' in url:
            # V1 URL structure: /#!<id>!<key>
            parts = url.split('#!')[1].split('!')
            if len(parts) >= 2:
                return parts[0].strip(), parts[1].strip()
        
        # Fallback to mega.py internal parser
        parsed = self._client._parse_url(url)
        split_p = parsed.split('!')
        return split_p[0], split_p[1]

    def get_file_info(self, url: str) -> Dict[str, Any]:
        """
        Fetches metadata for a MEGA file without downloading it.
        """
        file_handle, file_key_b64 = self.parse_url(url)
        file_key = base64_to_a32(file_key_b64)
        
        file_data = self._client._api_request({'a': 'g', 'g': 1, 'p': file_handle})
        if not file_data or 'g' not in file_data:
            err = file_data if isinstance(file_data, int) else "File not accessible"
            raise ValueError(f"MEGA API Error: {err}. Link might be dead, quota exceeded, or invalid.")

        file_url = file_data['g']
        file_size = file_data.get('s', 0)
        
        k = (file_key[0] ^ file_key[4], file_key[1] ^ file_key[5],
             file_key[2] ^ file_key[6], file_key[3] ^ file_key[7])
        iv = file_key[4:6] + (0, 0)
        meta_mac = file_key[6:8]
        
        attribs = base64_url_decode(file_data['at'])
        attribs = decrypt_attr(attribs, k)
        file_name = attribs.get('n', f"mega_{file_handle}.bin")

        # Determine file type / extension
        ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        
        return {
            "file_handle": file_handle,
            "file_key_b64": file_key_b64,
            "file_url": file_url,
            "file_size": file_size,
            "file_name": file_name,
            "file_extension": ext,
            "k": k,
            "iv": iv,
            "meta_mac": meta_mac
        }

    def create_decryptor(self, k, iv):
        k_str = a32_to_str(k)
        counter = Counter.new(128, initial_value=((iv[0] << 32) + iv[1]) << 64)
        aes = AES.new(k_str, AES.MODE_CTR, counter=counter)
        return aes, k_str

    def stream_decrypted_chunks(self, info: Dict[str, Any]) -> Generator[bytes, None, None]:
        """
        Streams decrypted data chunks directly from MEGA CDN.
        """
        file_url = info['file_url']
        file_size = info['file_size']
        k = info['k']
        iv = info['iv']

        resp = requests.get(file_url, stream=True)
        resp.raise_for_status()
        input_stream = resp.raw

        aes, _ = self.create_decryptor(k, iv)

        for _, chunk_size in get_chunks(file_size):
            chunk = input_stream.read(chunk_size)
            if not chunk:
                break
            decrypted = aes.decrypt(chunk)
            yield decrypted
