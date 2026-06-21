import argparse
import os
import subprocess
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DASHBOARD_PATH = ROOT / "reports" / "dashboard.html"
BUILD_SCRIPT = ROOT / "scripts" / "build_dashboard.py"
WATCHED_FILES = [
    DATA_DIR / "health.csv",
    DATA_DIR / "food.csv",
    DATA_DIR / "exercise.csv",
    DATA_DIR / "sleep.csv",
]


def file_signature(path):
    if not path.exists():
        return None
    stat = path.stat()
    return (stat.st_mtime_ns, stat.st_size)


def data_signature():
    return tuple((path.name, file_signature(path)) for path in WATCHED_FILES)


def build_dashboard():
    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message)


def dashboard_version():
    if not DASHBOARD_PATH.exists():
        return "0"
    text = DASHBOARD_PATH.read_text(encoding="utf-8", errors="ignore")
    marker = 'data-version="'
    start = text.find(marker)
    if start == -1:
        return "0"
    start += len(marker)
    end = text.find('"', start)
    if end == -1:
        return "0"
    return text[start:end]


class DashboardServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class):
        super().__init__(server_address, handler_class)
        self.last_signature = data_signature()
        self.version = 0
        self.last_error = ""

    def refresh_if_needed(self):
        current_signature = data_signature()
        if current_signature == self.last_signature and DASHBOARD_PATH.exists():
            return False

        try:
            build_dashboard()
            self.last_error = ""
            self.version += 1
            self.last_signature = current_signature
            return True
        except RuntimeError as exc:
            self.last_error = str(exc)
            return False

    def handle_error(self, request, client_address):
        exc_type, _, _ = sys.exc_info()
        if exc_type in {BrokenPipeError, ConnectionResetError}:
            return
        super().handle_error(request, client_address)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format, *args):
        print(f"[fer-health-os] {self.address_string()} - {format % args}")

    def do_GET(self):
        if self.path in {"/", "/dashboard", "/dashboard.html"}:
            self.server.refresh_if_needed()
            self.path = "/reports/dashboard.html"
            return super().do_GET()

        if self.path == "/events":
            return self.send_events()

        if self.path == "/version":
            return self.send_version()

        self.server.refresh_if_needed()
        return super().do_GET()

    def send_version(self):
        self.server.refresh_if_needed()
        body = dashboard_version().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_events(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        last_seen_version = self.server.version
        while True:
            changed = self.server.refresh_if_needed()
            if changed and self.server.version != last_seen_version:
                last_seen_version = self.server.version
                if not self.write_event("dashboard-updated", str(last_seen_version)):
                    return
            elif self.server.last_error:
                if not self.write_event("dashboard-error", self.server.last_error):
                    return
                self.server.last_error = ""
            else:
                if not self.write_event("ping", str(int(time.time()))):
                    return
            time.sleep(1)

    def write_event(self, event, data):
        try:
            payload = f"event: {event}\ndata: {data}\n\n".encode("utf-8")
            self.wfile.write(payload)
            self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError):
            return False


def parser():
    arg_parser = argparse.ArgumentParser(description="Serve Fer Health OS dashboard with live reload.")
    arg_parser.add_argument("--host", default="127.0.0.1")
    arg_parser.add_argument("--port", type=int, default=8787)
    return arg_parser


def main():
    args = parser().parse_args()
    os.chdir(ROOT)
    build_dashboard()

    server = DashboardServer((args.host, args.port), Handler)
    print(f"Serving Fer Health OS dashboard at http://{args.host}:{args.port}/")
    print("Watching data/*.csv. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped Fer Health OS dashboard server.")


if __name__ == "__main__":
    main()
