"""Read-only local preview of raw-HTML Jekyll Markdown pages."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = (ROOT / unquote(urlsplit(self.path).path).lstrip("/")).resolve()
        if urlsplit(self.path).path == "/assets/js/course-ai-config.js":
            data = b'window.COURSE_AI_API_BASE="http://127.0.0.1:8766";'
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path.is_relative_to(ROOT) and path.suffix == ".md" and path.is_file():
            raw = path.read_text(encoding="utf-8")
            if raw.startswith("---\n"):
                raw = raw.split("---\n", 2)[-1]
            data = ("<!doctype html><html lang='zh-CN'><meta charset='utf-8'>" + raw + "</html>").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8765), PreviewHandler).serve_forever()
