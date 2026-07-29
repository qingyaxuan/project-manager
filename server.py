"""Project Manager — Simple on-demand HTTP Server + API.
Usage: python server.py
Then open http://localhost:8765/web-ui/index.html
Press Ctrl+C to stop.
"""
import http.server
import json
import os
import secrets
import shutil
import subprocess
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
BUNDLE_DIR = Path(__file__).parent
STATIC_DIR = BUNDLE_DIR
DATA_FILE = BUNDLE_DIR / "projects-data.json"
INDEX_HTML = STATIC_DIR / "web-ui" / "index.html"
PORT = 8765
CLAUDE_CMD = r"C:\Users\qingy\AppData\Roaming\npm\claude.cmd"
DEFAULT_PROJECT_DIR = r"D:\Claude program"

# ── Ensure data file exists on first run ──
if not DATA_FILE.exists():
    DATA_FILE.write_text(
        json.dumps({"projects": [], "metadata": {"lastUpdated": "", "totalProjects": 0}},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _generate_id():
    """Generate a unique project ID: proj-YYYYMMDD-xxxx"""
    today = datetime.now().strftime("%Y%m%d")
    suffix = secrets.token_hex(2)
    return f"proj-{today}-{suffix}"


def _read_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(filepath, data):
    tmp = str(filepath) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, filepath)


def _sync_embedded_html(projects_data):
    """Update the embedded JSON data inside index.html for offline access.
    Uses string slicing (NOT re.sub) because regex replacement corrupts
    JSON backslash escapes like \\claude, \\PPT, etc."""
    if not INDEX_HTML.exists():
        return
    html = INDEX_HTML.read_text(encoding="utf-8")
    import re
    tag = r'<script\s+id="embedded-data"\s+type="application/json">'
    end = r'</script>'
    match = re.search(tag + r'(.*?)' + end, html, flags=re.DOTALL)
    if not match:
        return
    compact = json.dumps(projects_data, ensure_ascii=False)
    # Slice to avoid re.sub's backslash interpretation in replacement
    new_html = html[:match.start(1)] + compact + html[match.end(1):]
    if new_html != html:
        INDEX_HTML.write_text(new_html, encoding="utf-8")


def _update_metadata(data):
    data["metadata"]["lastUpdated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
    data["metadata"]["totalProjects"] = len(data.get("projects", []))
    return data


class ProjectServer(http.server.SimpleHTTPRequestHandler):
    """Serves static files + JSON API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    # ── CORS & logging ────────────────────────────────────────────
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write(f"  [{self.command}] {fmt % args}\n")

    # ── Routing ───────────────────────────────────────────────────
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = dict(urllib.parse.parse_qsl(parsed.query))

        if path == "/api/projects":
            self._api_list()
        elif path == "/api/scan":
            self._api_scan()
        elif path == "/api/open":
            self._api_open(params)
        elif path == "/api/continue":
            self._api_continue(params)
        elif path == "/api/status":
            self._api_status()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/api/projects":
            self._api_create()
        else:
            self._error("Not found", 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/projects/") and len(path) > len("/api/projects/"):
            self._api_update(path[len("/api/projects/"):])
        else:
            self._error("Not found", 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/projects/") and len(path) > len("/api/projects/"):
            self._api_delete(path[len("/api/projects/"):])
        else:
            self._error("Not found", 404)

    # ── GET handlers ──────────────────────────────────────────────
    def _api_list(self):
        try:
            data = _read_json(DATA_FILE)
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
            os.startfile(path)
            self._ok({"opened": True, "path": path})
        else:
            self._ok({"opened": False, "error": f"Path not found: {path}"})

    def _api_continue(self, params):
        """Open folder + launch Claude Code in project directory."""
        name = params.get("name", "")
        path = params.get("path", "")
        result = {"name": name, "path": path}
        CREATENOWIN = 0x08000000

        if not path or not os.path.exists(path):
            result["opened"] = False
            result["error"] = f"Path not found: {path}"
            self._ok(result)
            return

        prompt = f"继续开发 {name}"
        launched = False

        # Try Windows Terminal first
        try:
            wt_check = subprocess.run(
                ["where", "wt"], capture_output=True, timeout=5,
                creationflags=CREATENOWIN
            )
            if wt_check.returncode == 0:
                subprocess.Popen(
                    ["wt", "-d", path, "cmd", "/k",
                     f'set CLAUDE_CODE_CHILD_SESSION= && ""{CLAUDE_CMD}"" ""{prompt}"""'],
                    creationflags=CREATENOWIN,
                )
                launched = True
        except Exception:
            pass

        # Fallback: regular cmd window
        if not launched:
            try:
                subprocess.Popen(
                    ["cmd", "/c", "start", f'"Claude - {name}"', "cmd", "/k",
                     f'cd /d "{path}" && set CLAUDE_CODE_CHILD_SESSION= && ""{CLAUDE_CMD}"" ""{prompt}"""'],
                    creationflags=CREATENOWIN,
                )
                launched = True
            except Exception:
                pass

        result["opened"] = True
        result["launched"] = launched
        self._ok(result)

    def _api_status(self):
        try:
            data = _read_json(DATA_FILE)
            total = len(data.get("projects", []))
            self._ok({"running": True, "totalProjects": total})
        except Exception:
            self._ok({"running": True, "totalProjects": 0})

    def _api_scan(self):
        """Scan DEFAULT_PROJECT_DIR for directories not yet tracked."""
        untracked = []
        if os.path.isdir(DEFAULT_PROJECT_DIR):
            try:
                data = _read_json(DATA_FILE)
                known = set()
                for p in data.get("projects", []):
                    loc = p.get("location", "")
                    if loc:
                        known.add(Path(loc).resolve())
                for entry in os.listdir(DEFAULT_PROJECT_DIR):
                    full = Path(DEFAULT_PROJECT_DIR) / entry
                    if full.is_dir() and full.resolve() not in known:
                        untracked.append({
                            "name": entry,
                            "path": str(full),
                            "suggestion": entry.replace("_", " ").replace("-", " ")
                        })
            except Exception as exc:
                self._error(f"Scan failed: {exc}")
                return
        self._ok({"untracked": untracked, "watchDir": DEFAULT_PROJECT_DIR})

    # ── POST/PUT/DELETE handlers ─────────────────────────────────
    def _api_create(self):
        try:
            body = self._read_body()
            incoming = json.loads(body) if isinstance(body, str) else body
        except Exception:
            self._error("Invalid JSON body", 400)
            return

        name = (incoming.get("name") or "").strip()
        if not name:
            self._error("Project name is required", 400)
            return

        today = datetime.now().strftime("%Y-%m-%d")
        project = {
            "id": _generate_id(),
            "name": name,
            "description": (incoming.get("description") or "").strip(),
            "techStack": incoming.get("techStack") or [],
            "tags": incoming.get("tags") or [],
            "category": incoming.get("category") or "other",
            "createdAt": today,
            "updatedAt": today,
            "status": incoming.get("status") or "in-progress",
            "location": (incoming.get("location") or "").strip(),
            "highlights": incoming.get("highlights") or [],
        }

        try:
            data = _read_json(DATA_FILE)
            data.setdefault("projects", []).append(project)
            data = _update_metadata(data)
            _write_json(DATA_FILE, data)
            _sync_embedded_html(data)
            self._ok(project, 201)
        except Exception as exc:
            self._error(f"Failed to save: {exc}")

    def _api_update(self, proj_id):
        try:
            body = self._read_body()
            updates = json.loads(body) if isinstance(body, str) else body
        except Exception:
            self._error("Invalid JSON body", 400)
            return

        try:
            data = _read_json(DATA_FILE)
            projects = data.get("projects", [])
            idx = next((i for i, p in enumerate(projects) if p.get("id") == proj_id), None)
            if idx is None:
                self._error(f"Project not found: {proj_id}", 404)
                return

            allowed = {"name", "description", "techStack", "tags", "category",
                       "status", "location", "highlights"}
            for key in allowed:
                if key in updates:
                    projects[idx][key] = updates[key]

            projects[idx]["updatedAt"] = datetime.now().strftime("%Y-%m-%d")
            data = _update_metadata(data)
            _write_json(DATA_FILE, data)
            _sync_embedded_html(data)
            self._ok(projects[idx])
        except Exception as exc:
            self._error(f"Failed to update: {exc}")

    def _api_delete(self, proj_id):
        """Delete a project by ID. Also deletes directory if under DEFAULT_PROJECT_DIR."""
        try:
            data = _read_json(DATA_FILE)
            projects = data.get("projects", [])
            idx = next((i for i, p in enumerate(projects) if p.get("id") == proj_id), None)
            if idx is None:
                self._error(f"Project not found: {proj_id}", 404)
                return

            removed = projects.pop(idx)
            data = _update_metadata(data)
            _write_json(DATA_FILE, data)
            _sync_embedded_html(data)

            # Delete project directory if under default project dir
            location = removed.get("location", "")
            deleted_dir = False
            if location:
                loc_path = Path(location).resolve()
                default_path = Path(DEFAULT_PROJECT_DIR).resolve()
                try:
                    loc_str = str(loc_path) + "\\"
                    default_str = str(default_path) + "\\"
                    if loc_str.startswith(default_str) and loc_path.is_dir():
                        shutil.rmtree(loc_path)
                        deleted_dir = True
                except Exception:
                    pass

            self._ok({
                "deleted": True, "id": proj_id,
                "name": removed.get("name", ""), "deletedDir": deleted_dir
            })
        except Exception as exc:
            self._error(f"Failed to delete: {exc}")

    # ── Helpers ───────────────────────────────────────────────────
    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return "{}"
        return self.rfile.read(length).decode("utf-8")

    def _ok(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, msg, code=500):
        body = json.dumps({"error": msg}, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    os.chdir(str(STATIC_DIR))

    print(f"\n  ◆ Project Manager Server")
    print(f"  Web UI: http://localhost:{PORT}/web-ui/index.html")
    print(f"  Data:   {DATA_FILE}")
    print(f"  Watch:  {DEFAULT_PROJECT_DIR}")
    print(f"  Press Ctrl+C to stop.\n")

    try:
        server = http.server.HTTPServer(("0.0.0.0", PORT), ProjectServer)
    except OSError:
        print(f"  Port {PORT} is already in use. Server may already be running.")
        sys.exit(0)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()
