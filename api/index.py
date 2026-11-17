import sys
import os
import urllib.parse

# Đảm bảo thư mục gốc dự án luôn nằm trong sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import ThienMinhRequestHandler

class handler(ThienMinhRequestHandler):
    """
    Entrypoint Serverless Function cho Vercel.
    Kế thừa toàn bộ logic xử lý từ ThienMinhRequestHandler.
    """
    def do_GET(self):
        self._normalize_vercel_path()
        return super().do_GET()

    def do_POST(self):
        self._normalize_vercel_path()
        return super().do_POST()

    def do_OPTIONS(self):
        self._normalize_vercel_path()
        return super().do_OPTIONS()

    def _normalize_vercel_path(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        # Nếu Vercel rewrite đường dẫn qua ?__route=...
        if '__route' in qs:
            route = qs['__route'][0]
            other_qs = {k: v for k, v in qs.items() if k != '__route'}
            new_query = urllib.parse.urlencode(other_qs, doseq=True)
            self.path = ('/api/' + route.lstrip('/')) + (f"?{new_query}" if new_query else "")
