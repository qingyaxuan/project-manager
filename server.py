"""Project Manager — HTTP Server + API, PyInstaller-compatible."""
import http.server
import json
import os
import subprocess
import sys
import urllib.parse
from pathlib import Path

# ── Paths: handle both dev (script) and frozen (PyInstaller EXE) modes ──
if getattr(sys, 'frozen', False):
    # Running as compiled EXE — static files live in the bundle temp dir
    BUNDLE_DIR = Path(sys.executable).parent   # writable, next to EXE
    STATIC_DIR = Path(sys._MEIPASS)            # read-only, bundled assets
else:
    BUNDLE_DIR = Path(__file__).parent
    STATIC_DIR = BUNDLE_DIR

DATA_FILE = BUNDLE_DIR / "projects-data.json"
PORT = 8765
CLAUDE_CMD = r"C:\Users\qingy\AppData\Roaming\npm\claude.cmd"

# ── Ensure data file exists on first run ──
if not DATA_FILE.exists():
    DATA_FILE.write_text(
        json.dumps({"projects": [], "metadata": {"lastUpdated": "", "totalProjects": 0}},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class ProjectServer(http.server.SimpleHTTPRequestHandler):
    """Serves static files from STATIC_DIR + JSON API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    # ── CORS & logging ──────────────────────────────────────────────
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write(f"  [{self.command}] {fmt % args}\n")

    # ── Routing ─────────────────────────────────────────────────────
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = dict(urllib.parse.parse_qsl(parsed.query))

        if path == "/api/projects":
            self._serve_json(DATA_FILE)
        elif path == "/api/open":
            self._api_open(params)
        elif path == "/api/continue":
            self._api_continue(params)
        elif path == "/api/status":
            self._api_status()
        else:
            super().do_GET()

    # ── API handlers ────────────────────────────────────────────────
    def _serve_json(self, filepath):
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            self._error(str(exc))

    def _api_open(self, params):
        """Open a project folder in File Explorer."""
        path = params.get("path", "")
        if path and os.path.exists(path):
            subprocess.Popen(["explorer", path], shell=True)
            self._ok({"opened": True, "path": path})
        else:
            self._ok({"opened": False, "error": f"Path not found: {path}"})

    def _api_continue(self, params):
        """Open folder + launch Claude Code in project directory."""
        name = params.get("name", "")
        path = params.get("path", "")
        result = {"name": name, "path": path}

        if not path or not os.path.exists(path):
            result["opened"] = False
            result["error"] = f"Path not found: {path}"
            self._ok(result)
            return

        prompt = f"继续开发 {name}"
        launched = False

        # Try Windows Terminal first
        try:
            if os.system("where wt >nul 2>&1") == 0:
                subprocess.Popen(
                    f'wt -d "{path}" cmd /k "set CLAUDE_CODE_CHILD_SESSION= && ""{CLAUDE_CMD}"" ""{prompt}"""',
                    shell=True,
                )
                launched = True
        except Exception:
            pass

        # Fallback: regular cmd window
        if not launched:
            try:
                subprocess.Popen(
                    f'start "Claude - {name}" cmd /k "cd /d {path} && set CLAUDE_CODE_CHILD_SESSION= && ""{CLAUDE_CMD}"" ""{prompt}"""',
                    shell=True,
                )
                launched = True
            except Exception:
                pass

        result["opened"] = True
        result["launched"] = launched
        self._ok(result)

    def _api_status(self):
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            total = len(data.get("projects", []))
            self._ok({"running": True, "totalProjects": total})
        except Exception:
            self._ok({"running": True, "totalProjects": 0, "error": "Data unreadable"})

    # ── Helpers ─────────────────────────────────────────────────────
    def _ok(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, msg):
        body = json.dumps({"error": msg}, ensure_ascii=False).encode("utf-8")
        self.send_response(500)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    os.chdir(str(STATIC_DIR))
    print(f"\n  Project Manager Server")
    print(f"  Web: http://localhost:{PORT}/web-ui/index.html")
    print(f"  API: /api/projects | /api/open | /api/continue | /api/status")
    print(f"  Data: {DATA_FILE}")
    print(f"  Press Ctrl+C to stop.\n")

    server = http.server.HTTPServer(("0.0.0.0", PORT), ProjectServer)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()
