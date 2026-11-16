#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys

PORT = 8080
HUD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ui", "shell-hud"))

class HUDRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HUD_DIR, **kwargs)

    def do_GET(self):
        # Handle /ui/shell-hud prefix gracefully if user pasted it
        if self.path.startswith("/ui/shell-hud"):
            self.path = self.path[len("/ui/shell-hud"):] or "/"
        super().do_GET()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("0.0.0.0", port), HUDRequestHandler) as httpd:
            print("==================================================")
            print(f"  AetherOS AI HUD Server Live on Port {port}")
            print(f"  Open: http://localhost:{port}")
            print(f"  Directory: {HUD_DIR}")
            print("==================================================")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98: # Address already in use
            # Try port 8081
            port = 8081
            with socketserver.TCPServer(("0.0.0.0", port), HUDRequestHandler) as httpd:
                print(f"  Port 8080 was busy. Switched to http://localhost:{port}")
                httpd.serve_forever()
        else:
            raise
